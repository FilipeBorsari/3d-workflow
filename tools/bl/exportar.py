"""Exportação de peças (STL em mm) e do .blend."""
from pathlib import Path

import bpy

from . import malha


def stl(objs, caminho):
    """Exporta os objetos (modificadores aplicados) para um único STL em mm.

    Triangula antes (BEAUTY, como a checagem): deixar o exportador triangular n-gonos
    côncavos de booleanas pode criar arestas com 4 faces ("manifold = no" no Bambu).
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporarios = []
    for o in objs:
        if o.type == "MESH":
            mod = o.modifiers.new("_triangular_stl", "TRIANGULATE")
            mod.quad_method = "BEAUTY"
            mod.ngon_method = "BEAUTY"
            temporarios.append((o, mod))
    malha.selecionar(objs)
    try:
        _exportar(caminho)
    finally:
        for o, mod in temporarios:
            o.modifiers.remove(mod)
    return caminho


def _exportar(caminho):
    bpy.ops.wm.stl_export(
        filepath=str(caminho),
        export_selected_objects=True,
        apply_modifiers=True,
        global_scale=1.0,
        use_scene_unit=False,
        ascii_format=False,
    )


def stl_por_peca(objs, pasta):
    """Um STL por objeto: <pasta>/<nome do objeto>.stl."""
    return [stl([o], Path(pasta) / f"{o.name}.stl") for o in objs]


def blend(caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(caminho), copy=True)
    return caminho
