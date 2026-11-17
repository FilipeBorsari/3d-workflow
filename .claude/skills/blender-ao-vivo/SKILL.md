---
name: blender-ao-vivo
description: Controla o Blender que o usuário está com a interface aberta, pela ponte local (tools/blender_ponte) — consulta a cena, seleção e objetos, roda código ou o modelo.py e tira print do viewport para ver o que o usuário vê. Use quando o usuário disser que está com o Blender aberto, pedir para "ver a cena", "mexer no que está selecionado", "mostrar no Blender", ou quiser acompanhar a modelagem ao vivo.
---

# Blender ao vivo (ponte)

A ponte é um servidor em `127.0.0.1:9876` dentro do Blender aberto
(`tools/blender_ponte/claude_ponte.py`). O código roda na thread principal do Blender.

## 1. Verificar a ponte

```bash
python3 tools/blender_ponte/cliente.py --status
```

- Código de saída 3 = ponte inacessível. Então:
  - Ponte nunca instalada: rode `tools/blender_ponte/instalar.sh` (cria link simbólico em
    `~/.config/blender/<versão>/scripts/startup/`). Peça ao usuário para reiniciar o Blender.
  - Instalada, mas parada: peça ao usuário para clicar em **Iniciar** em
    Viewport 3D > tecla N > aba **Claude**.
  - Blender fechado: abra para o usuário com `blender >/dev/null 2>&1 &`
    (ou um .blend: `blender "caminho.blend" >/dev/null 2>&1 &`) e espere ~5 s.

## 2. Comandos

```bash
C() { python3 tools/blender_ponte/cliente.py "$@"; }   # função: funciona em bash e zsh
C --status                                   # versão, arquivo, objetos, seleção
C -c "print(bpy.context.active_object.dimensions)"
C -c "from bl import checagem; checagem.relatorio(bpy.context.selected_objects)"
C projetos/<nome>/modelo.py                  # roda o modelo no Blender aberto
C --captura /tmp/claude-viewport.png         # depois use Read na imagem
```

- Código com `-c` roda num namespace persistente: variáveis ficam para a próxima chamada.
- Arquivo `.py` roda isolado (`runpy`, `__name__ == "__main__"`) e o pacote `bl` é
  recarregado do disco a cada execução.
- `print()` volta para o terminal. Exceção volta como traceback e código de saída 1.
- Timeout padrão 300 s (`--timeout`). Timeout costuma significar Blender ocupado ou
  janela modal aberta (diálogo de salvar, por exemplo).

## 3. Cuidados

- `cena.nova_cena()` (chamada no início de todo `modelo.py`) APAGA os objetos da cena
  aberta. Antes de rodar um modelo na sessão ao vivo, confira `--status`. Se houver
  objetos que não vieram do modelo ou arquivo não salvo, pergunte ao usuário.
- Não salve por cima do .blend do usuário sem pedir. Para salvar uma cópia:
  `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)`.
- Prefira editar dados (`obj.location`, `obj.data`, modificadores) a `bpy.ops`.
  Operadores de viewport precisam de `bpy.context.temp_override(window=, area=, region=)`.
- Mudanças feitas ao vivo e que devem durar precisam ir para o `modelo.py`. O .blend
  aberto não é a fonte da verdade, a menos que o README do projeto diga o contrário.
- A ponte executa qualquer código Python enviado por processos locais. Ela é desligada
  pelo painel (aba Claude) ou removida com `tools/blender_ponte/instalar.sh --remover`.

## 4. Modo headless persistente (sem interface)

Útil para muitas consultas seguidas sem pagar a inicialização do Blender a cada vez:

```bash
blender -b --factory-startup -P tools/blender_ponte/claude_ponte.py &   # rode em background
python3 tools/blender_ponte/cliente.py -c "..."
```

`--captura` não funciona nesse modo (não há janela). Use `preview.renderizar`.
