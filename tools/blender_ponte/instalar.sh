#!/usr/bin/env bash
# Instala a ponte Claude como script de startup do Blender (link simbólico).
# Depois disso, todo Blender aberto com interface sobe a ponte em 127.0.0.1:9876.
#
# Uso: tools/blender_ponte/instalar.sh            # instala
#      tools/blender_ponte/instalar.sh --remover  # remove
set -euo pipefail

BLENDER="${BLENDER:-blender}"
ORIGEM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/claude_ponte.py"
DESTINO_DIR="$("$BLENDER" -b --factory-startup --python-expr \
  "import bpy; print('STARTUP=' + bpy.utils.user_resource('SCRIPTS', path='startup', create=True))" 2>/dev/null \
  | sed -n 's/^STARTUP=//p')"

if [[ -z "$DESTINO_DIR" ]]; then
  echo "ERRO: não consegui descobrir a pasta de scripts do Blender." >&2
  exit 1
fi
DESTINO="$DESTINO_DIR/claude_ponte.py"

if [[ "${1:-}" == "--remover" ]]; then
  rm -f "$DESTINO"
  echo "Ponte removida de $DESTINO"
  exit 0
fi

mkdir -p "$DESTINO_DIR"
ln -sf "$ORIGEM" "$DESTINO"
echo "Ponte instalada: $DESTINO -> $ORIGEM"
echo "Reinicie o Blender. Painel: Viewport 3D > N > aba Claude."
