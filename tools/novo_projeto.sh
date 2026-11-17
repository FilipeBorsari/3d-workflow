#!/usr/bin/env bash
# Cria um projeto novo a partir de projetos/_modelo.
#
# Uso: tools/novo_projeto.sh <nome-em-kebab-case> ["Descrição curta"]
#      tools/novo_projeto.sh suporte-celular "Suporte de mesa para celular"
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOME="${1:?uso: tools/novo_projeto.sh <nome-em-kebab-case> [\"Descrição\"]}"
DESCRICAO="${2:-}"

if [[ ! "$NOME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "ERRO: use kebab-case sem acentos (ex.: suporte-celular)" >&2
  exit 1
fi

DESTINO="$RAIZ/projetos/$NOME"
if [[ -e "$DESTINO" ]]; then
  echo "ERRO: $DESTINO já existe" >&2
  exit 1
fi

cp -r "$RAIZ/projetos/_modelo" "$DESTINO"
rm -rf "$DESTINO/saida"/* 2>/dev/null || true
sed -i "s/NOME DO PROJETO/$NOME/; s#projetos/NOME/#projetos/$NOME/#" "$DESTINO/modelo.py"
DESCRICAO_SED="$(printf '%s' "${DESCRICAO:-Descreva o objetivo da peça.}" | sed 's/[&|\\]/\\&/g')"
sed -i "s|^# NOME DO PROJETO|# $NOME|; s|^DESCRICAO_CURTA|$DESCRICAO_SED|" "$DESTINO/README.md"
sed -i "s/^- Criado em: .*/- Criado em: $(date +%Y-%m-%d)/" "$DESTINO/README.md"
echo "Projeto criado: projetos/$NOME"
