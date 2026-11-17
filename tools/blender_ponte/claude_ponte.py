"""Ponte Claude <-> Blender aberto.

Servidor TCP local (127.0.0.1) dentro do Blender. Recebe código Python, executa
na thread principal (seguro para bpy) e devolve stdout/erro em JSON.
O cliente é tools/blender_ponte/cliente.py.

Modos:
- Blender com interface: instalado como script de startup (tools/blender_ponte/instalar.sh),
  sobe sozinho ao abrir o Blender.
- Headless persistente: blender -b -P tools/blender_ponte/claude_ponte.py
  (mantém a cena viva entre comandos; útil para testes).

Segurança: aceita conexões só de 127.0.0.1, mas qualquer processo local pode
executar código no Blender enquanto a ponte estiver ativa.
Protocolo: uma linha JSON {"codigo": str, "timeout": s} -> uma linha JSON
{"ok": bool, "saida": str, "erro": str|None}.
"""
import contextlib
import io
import json
import os
import queue
import socket
import sys
import threading
import time
import traceback
from pathlib import Path

import bpy

bl_info = {
    "name": "Claude Ponte",
    "author": "projetos 3d",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "category": "Development",
    "description": "Servidor local para o Claude Code executar código no Blender aberto",
}

HOST = "127.0.0.1"
PORTA = int(os.environ.get("CLAUDE_PONTE_PORTA", "9876"))

_fila = queue.Queue()
_estado = {"socket": None, "ativo": False}
# Namespace persistente: variáveis criadas num comando continuam no próximo.
_ns = {"bpy": bpy, "__name__": "__claude_ponte__"}


def _caminho_repo_tools():
    """Põe tools/ do repositório no sys.path (para `from bl import ...`)."""
    real = Path(__file__).resolve()
    tools = real.parent.parent
    if (tools / "bl").is_dir() and str(tools) not in sys.path:
        sys.path.insert(0, str(tools))


def _executar(codigo):
    saida = io.StringIO()
    try:
        with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
            exec(compile(codigo, "<claude_ponte>", "exec"), _ns)
        return {"ok": True, "saida": saida.getvalue(), "erro": None}
    except Exception:
        return {"ok": False, "saida": saida.getvalue(), "erro": traceback.format_exc()}


def _processar_fila():
    while True:
        try:
            codigo, resposta = _fila.get_nowait()
        except queue.Empty:
            break
        resposta.put(_executar(codigo))
    return 0.05 if _estado["ativo"] else None


def _atender(conexao):
    with conexao:
        dados = b""
        while not dados.endswith(b"\n"):
            parte = conexao.recv(1 << 16)
            if not parte:
                break
            dados += parte
        try:
            pedido = json.loads(dados or b"{}")
            resposta = queue.Queue()
            _fila.put((pedido["codigo"], resposta))
            resultado = resposta.get(timeout=float(pedido.get("timeout", 300)))
        except queue.Empty:
            resultado = {"ok": False, "saida": "", "erro": "timeout esperando o Blender (ocupado ou modal aberto?)"}
        except Exception:
            resultado = {"ok": False, "saida": "", "erro": traceback.format_exc()}
        conexao.sendall((json.dumps(resultado) + "\n").encode())


def _aceitar(servidor):
    while _estado["ativo"]:
        try:
            conexao, _ = servidor.accept()
        except OSError:
            break
        threading.Thread(target=_atender, args=(conexao,), daemon=True).start()


def iniciar():
    if _estado["ativo"]:
        return True
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        servidor.bind((HOST, PORTA))
    except OSError as erro:
        print(f"[claude_ponte] porta {PORTA} ocupada ({erro}); ponte não iniciada")
        servidor.close()
        return False
    servidor.listen(4)
    _estado.update(socket=servidor, ativo=True)
    threading.Thread(target=_aceitar, args=(servidor,), daemon=True).start()
    if not bpy.app.background:
        bpy.app.timers.register(_processar_fila, persistent=True)
    print(f"[claude_ponte] ouvindo em {HOST}:{PORTA}")
    return True


def parar():
    _estado["ativo"] = False
    if _estado["socket"]:
        _estado["socket"].close()
        _estado["socket"] = None
    if bpy.app.timers.is_registered(_processar_fila):
        bpy.app.timers.unregister(_processar_fila)
    print("[claude_ponte] parada")


class CLAUDE_OT_ponte(bpy.types.Operator):
    bl_idname = "claude.ponte_alternar"
    bl_label = "Ligar/desligar ponte Claude"

    def execute(self, context):
        parar() if _estado["ativo"] else iniciar()
        return {"FINISHED"}


class CLAUDE_PT_ponte(bpy.types.Panel):
    bl_label = "Claude"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Claude"

    def draw(self, context):
        ativo = _estado["ativo"]
        self.layout.label(text=f"Ponte: {'ativa' if ativo else 'parada'} ({HOST}:{PORTA})")
        self.layout.operator(CLAUDE_OT_ponte.bl_idname, text="Parar" if ativo else "Iniciar",
                             icon="PAUSE" if ativo else "PLAY")


def register():
    _caminho_repo_tools()
    bpy.utils.register_class(CLAUDE_OT_ponte)
    bpy.utils.register_class(CLAUDE_PT_ponte)
    if not bpy.app.background and os.environ.get("CLAUDE_PONTE_AUTO", "1") == "1":
        iniciar()


def unregister():
    parar()
    bpy.utils.unregister_class(CLAUDE_PT_ponte)
    bpy.utils.unregister_class(CLAUDE_OT_ponte)


if __name__ == "__main__" and bpy.app.background:
    # Headless persistente: processa a fila na thread principal até Ctrl+C.
    _caminho_repo_tools()
    if iniciar():
        try:
            while _estado["ativo"]:
                _processar_fila()
                time.sleep(0.05)
        except KeyboardInterrupt:
            parar()
