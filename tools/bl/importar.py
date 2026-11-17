"""Importação de formatos que o Blender não lê sozinho (3MF)."""
import re
import zipfile
from pathlib import Path

import bpy
import numpy as np

_VERTICE = re.compile(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"')
_TRIANGULO = re.compile(rb'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"')


def malha_3mf(caminho, nome=None):
    """Lê as malhas de um 3MF (todos os <object> com <mesh>, em mm) num objeto só.

    Ignora cores/materiais e transformações de <item>/<component>: serve para 3MF exportado
    de outro programa (uma malha por objeto). Projeto do Bambu Studio com peças montadas
    por componentes precisa de outro caminho.
    """
    caminho = Path(caminho)
    verts, tris = [], []
    with zipfile.ZipFile(caminho) as z:
        for arq in z.namelist():
            if not arq.lower().endswith(".model"):
                continue
            texto = z.read(arq)
            for bloco in re.findall(rb"<mesh>(.*?)</mesh>", texto, re.S):
                v = np.array(_VERTICE.findall(bloco), dtype=np.float64)
                t = np.array(_TRIANGULO.findall(bloco), dtype=np.int64)
                if len(v) and len(t):
                    tris.append(t + sum(len(x) for x in verts))
                    verts.append(v)
    if not verts:
        raise ValueError(f"nenhuma malha em {caminho}")
    v = np.vstack(verts)
    t = np.vstack(tris)
    dados = bpy.data.meshes.new(nome or caminho.stem)
    dados.vertices.add(len(v))
    dados.vertices.foreach_set("co", v.astype(np.float32).ravel())
    dados.loops.add(t.size)
    dados.loops.foreach_set("vertex_index", t.astype(np.int32).ravel())
    dados.polygons.add(len(t))
    dados.polygons.foreach_set("loop_start", np.arange(0, t.size, 3, dtype=np.int32))
    dados.update()
    dados.validate()
    obj = bpy.data.objects.new(dados.name, dados)
    bpy.context.scene.collection.objects.link(obj)
    return obj
