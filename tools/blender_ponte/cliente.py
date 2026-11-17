#!/usr/bin/env python3
"""Cliente da ponte Claude <-> Blender aberto (ver claude_ponte.py).

Uso:
    python3 tools/blender_ponte/cliente.py --status
    python3 tools/blender_ponte/cliente.py -c "print([o.name for o in bpy.data.objects])"
    python3 tools/blender_ponte/cliente.py projetos/x/modelo.py      # roda arquivo como __main__
    python3 tools/blender_ponte/cliente.py --captura /tmp/viewport.png  # print do viewport 3D

Código enviado com -c roda num namespace persistente (variáveis sobrevivem entre chamadas).
Arquivos rodam isolados via runpy, com o pacote `bl` recarregado do disco.
Sai com código 1 se o Blender devolver erro, 3 se a ponte não estiver acessível.
"""
import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path

HOST = "127.0.0.1"
PORTA = int(os.environ.get("CLAUDE_PONTE_PORTA", "9876"))

CODIGO_STATUS = """
import bpy
print(json.dumps({
    "blender": bpy.app.version_string,
    "arquivo": bpy.data.filepath or None,
    "cena": bpy.context.scene.name,
    "objetos": [{"nome": o.name, "tipo": o.type, "dimensoes_mm": [round(d, 2) for d in o.dimensions]}
                for o in bpy.context.scene.objects],
    "selecionados": [o.name for o in bpy.context.selected_objects],
    "ativo": bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,
}, ensure_ascii=False, indent=1))
"""

_AREA_3D = """
import bpy
janela = bpy.context.window_manager.windows[0]
areas = [a for a in janela.screen.areas if a.type == "VIEW_3D"]
if not areas:
    raise RuntimeError("nenhuma área 3D visível na janela principal")
area = max(areas, key=lambda a: a.width * a.height)
regiao = next(r for r in area.regions if r.type == "WINDOW")
"""

# Enquadrar e capturar vão em chamadas separadas: o Blender precisa redesenhar entre
# as duas (capturar na mesma chamada gerou PNG de 1x1 px nos testes).
CODIGO_ENQUADRAR = _AREA_3D + """
area.spaces.active.clip_end = max(area.spaces.active.clip_end, 10000)
suave = bpy.context.preferences.view.smooth_view
bpy.context.preferences.view.smooth_view = 0
with bpy.context.temp_override(window=janela, screen=janela.screen, area=area, region=regiao):
    bpy.ops.view3d.view_all(center=False)
bpy.context.preferences.view.smooth_view = suave
area.tag_redraw()
"""

CODIGO_CAPTURA = _AREA_3D + """
with bpy.context.temp_override(window=janela, screen=janela.screen, area=area, region=regiao):
    bpy.ops.screen.screenshot_area(filepath={caminho!r})
print({caminho!r})
"""

CODIGO_ARQUIVO = """
import runpy, sys
for _m in [m for m in sys.modules if m == "bl" or m.startswith("bl.")]:
    del sys.modules[_m]
runpy.run_path({caminho!r}, run_name="__main__")
"""


def enviar(codigo, timeout):
    try:
        with socket.create_connection((HOST, PORTA), timeout=5) as s:
            s.settimeout(timeout + 5)
            s.sendall((json.dumps({"codigo": codigo, "timeout": timeout}) + "\n").encode())
            dados = b""
            while not dados.endswith(b"\n"):
                parte = s.recv(1 << 16)
                if not parte:
                    break
                dados += parte
    except (ConnectionRefusedError, socket.timeout, OSError) as erro:
        print(f"ERRO: ponte inacessível em {HOST}:{PORTA} ({erro}).\n"
              "Abra o Blender com a ponte instalada (tools/blender_ponte/instalar.sh) "
              "ou ligue no painel N > Claude.", file=sys.stderr)
        sys.exit(3)
    return json.loads(dados)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("arquivo", nargs="?", help="script .py para rodar no Blender aberto")
    p.add_argument("-c", "--codigo", help="código Python para executar")
    p.add_argument("--status", action="store_true", help="resumo da cena aberta")
    p.add_argument("--captura", metavar="PNG", help="salva print do viewport 3D")
    p.add_argument("--sem-enquadrar", action="store_true",
                   help="com --captura: mantém a vista do usuário (padrão: enquadra todos os objetos)")
    p.add_argument("--timeout", type=float, default=300)
    args = p.parse_args()

    if args.status:
        codigo = "import json\n" + CODIGO_STATUS
    elif args.captura:
        if not args.sem_enquadrar:
            resultado = enviar(CODIGO_ENQUADRAR, args.timeout)
            if not resultado.get("ok"):
                print((resultado.get("erro") or "").rstrip(), file=sys.stderr)
                sys.exit(1)
            time.sleep(0.5)
        codigo = CODIGO_CAPTURA.format(caminho=str(Path(args.captura).resolve()))
    elif args.codigo:
        codigo = args.codigo
    elif args.arquivo:
        codigo = CODIGO_ARQUIVO.format(caminho=str(Path(args.arquivo).resolve()))
    else:
        p.error("informe um arquivo, -c, --status ou --captura")

    resultado = enviar(codigo, args.timeout)
    if resultado.get("saida"):
        print(resultado["saida"], end="")
    if not resultado.get("ok"):
        print((resultado.get("erro") or "").rstrip(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
