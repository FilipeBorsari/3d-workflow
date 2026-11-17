"""NOME DO PROJETO — modelo paramétrico (fonte da verdade da geometria).

Rodar:  tools/blender.sh projetos/NOME/modelo.py
Gera:   saida/<peça>.stl, saida/modelo.blend, saida/relatorio.json, saida/preview/folha.png

Todas as medidas em mm. Ajuste os parâmetros abaixo e rode de novo.
"""
from pathlib import Path

import bpy  # noqa: F401  (disponível para operações diretas)

from bl import cena, checagem, exportar, formas, malha, preview

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "saida"

# --- Parâmetros (mm) ---------------------------------------------------------
LARGURA = 40.0
PROFUNDIDADE = 30.0
ALTURA = 20.0
CHANFRO = 1.0


# --- Geometria ---------------------------------------------------------------
def construir():
    cena.nova_cena()

    peca = formas.caixa(LARGURA, PROFUNDIDADE, ALTURA, chanfro=CHANFRO, nome="peca")
    formas.furo_parafuso(peca, x=0, y=0, altura_peca=ALTURA)  # exemplo: furo M3 central

    malha.apoiar_na_mesa(peca)
    return [peca]


# --- Saída -------------------------------------------------------------------
if __name__ == "__main__":
    pecas = construir()
    exportar.stl_por_peca(pecas, SAIDA)
    exportar.blend(SAIDA / "modelo.blend")
    checagem.relatorio(pecas, SAIDA / "relatorio.json")
    print("PREVIEW:", preview.renderizar(pecas, SAIDA / "preview"))
