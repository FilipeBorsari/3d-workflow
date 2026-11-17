"""Inspeciona STL/OBJ/PLY/3MF/.blend: relatório de imprimibilidade + previews.

Uso (via wrapper headless):
    tools/blender.sh tools/inspecionar.py -- arquivo.stl [outro.stl] [--saida pasta]

Saída: <pasta>/relatorio.json e <pasta>/preview/folha.png (iso, frente, lado, topo).
Padrão de <pasta>: <pasta do 1º arquivo>/inspecao_<nome>.
"""
import argparse
import sys
from pathlib import Path

import bpy

from bl import cena, checagem, preview

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("arquivos", nargs="+")
p.add_argument("--saida")
args = p.parse_args(argv)

arquivos = [Path(a).resolve() for a in args.arquivos]
saida = Path(args.saida).resolve() if args.saida else arquivos[0].parent / f"inspecao_{arquivos[0].stem}"

if arquivos[0].suffix.lower() == ".blend":
    bpy.ops.wm.open_mainfile(filepath=str(arquivos[0]))
    cena.configurar_mm()
else:
    cena.nova_cena()
    importadores = {".stl": bpy.ops.wm.stl_import, ".obj": bpy.ops.wm.obj_import, ".ply": bpy.ops.wm.ply_import}
    for arquivo in arquivos:
        if arquivo.suffix.lower() == ".3mf":
            from bl import importar
            importar.malha_3mf(arquivo, arquivo.stem)
            continue
        importador = importadores.get(arquivo.suffix.lower())
        if not importador:
            sys.exit(f"formato não suportado: {arquivo.suffix}")
        importador(filepath=str(arquivo))

objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()]
checagem.relatorio(objs, saida / "relatorio.json")
print("PREVIEW:", preview.renderizar(objs, saida / "preview"))
