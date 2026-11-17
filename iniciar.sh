#!/usr/bin/env bash
# Inicia a Oficina 3D (interface visual) e abre o navegador.
set -euo pipefail
cd "$(dirname "$0")/app"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js não encontrado. Instale a versão 20 ou mais nova: https://nodejs.org" >&2
  exit 1
fi
if [[ ! -d node_modules ]]; then
  echo "Primeira execução: instalando dependências..."
  npm install --omit=dev
fi

PORTA="${PORTA:-3333}"
export PORTA
( sleep 2; xdg-open "http://localhost:$PORTA" >/dev/null 2>&1 || true ) &
exec node servidor.mjs
