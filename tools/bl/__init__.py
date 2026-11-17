"""Utilitários para scripts bpy deste repositório.

Disponível em scripts rodados por tools/blender.sh (o wrapper põe tools/ no sys.path):

    from bl import cena, malha, exportar, checagem, preview

Convenção: 1 unidade do Blender = 1 mm. Z para cima. Peça apoiada em Z=0.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
