#!/usr/bin/env bash
# Roda um script bpy no Blender sem interface (headless).
#
# Uso: tools/blender.sh <script.py> [-- args do script]
#      tools/blender.sh projetos/caneca/modelo.py
#      tools/blender.sh tools/inspecionar.py -- peca.stl --saida /tmp/inspecao
#
# - tools/ entra no sys.path: o script pode fazer `from bl import ...`
# - --factory-startup: ignora preferências/add-ons do usuário (resultado reproduzível)
# - Sai com código != 0 se o script levantar exceção
set -euo pipefail

BLENDER="${BLENDER:-blender}"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -lt 1 ]]; then
  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi

SCRIPT="$(realpath "$1")"
shift
# Windows (Git Bash): o Blender é um .exe e não entende /c/Users/...; converte para C:/Users/...
if command -v cygpath >/dev/null 2>&1; then
  RAIZ="$(cygpath -m "$RAIZ")"
  SCRIPT="$(cygpath -m "$SCRIPT")"
fi
[[ "${1:-}" == "--" ]] && shift

exec "$BLENDER" --background --factory-startup --python-exit-code 1 \
  --python-expr "import sys; sys.path.insert(0, '$RAIZ/tools')" \
  --python "$SCRIPT" -- "$@"
