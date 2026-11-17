"""Pintura multicor por triângulo, no formato do Bambu Studio (3MF com `paint_color`).

É o mesmo dado que a ferramenta de pintura multicor do Bambu Studio grava: cada triângulo
leva o número do filamento (1, 2, 3...). O fatiador espalha a cor da superfície para dentro
da peça. Serve para peças orgânicas (rosto, cabelo) em que separar cada cor numa parte por
booleana seria difícil.

    from bl import pintura
    cores = pintura.cores_vazias(obj)           # um inteiro por triângulo, 0 = filamento do objeto
    cores[mascara] = 2
    pintura.exportar_3mf(obj, cores, "saida/peca_pintada.3mf")

O objeto precisa estar triangulado (`pintura.triangular(obj)`); `cores` segue a ordem de
`obj.data.polygons`. Depois rode `tools/fatiar.py peca_pintada.3mf --filamento ... (um por cor)`.
"""
import zipfile
from pathlib import Path

import bmesh
import numpy as np

_TIPOS = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


def codigo(filamento):
    """Código `paint_color` de um triângulo inteiro (sem subdivisão) no filamento N.

    Formato do TriangleSelector do Bambu/Prusa: 2 bits de divisão (00) + 2 bits de estado;
    estado >= 3 vira '11' + 4 bits (estado - 3). Os nibbles saem em ordem invertida.
    1 -> '4', 2 -> '8', 3 -> '0C', 4 -> '1C', 5 -> '2C'... 0 = sem pintura.
    """
    if filamento <= 0:
        return ""
    if filamento < 3:
        return "%X" % (filamento << 2)
    if filamento > 16:
        raise ValueError("pintura aceita até 16 filamentos")
    return "%XC" % (filamento - 3)


def triangular(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3],
                          quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def cores_vazias(obj):
    return np.zeros(len(obj.data.polygons), dtype=np.int32)


def arrays_mundo(obj):
    """Vértices (coordenadas do mundo) e triângulos do objeto como arrays numpy."""
    me = obj.data
    v = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3)
    m = np.array(obj.matrix_world)
    v = v @ m[:3, :3].T + m[:3, 3]
    n = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_total", n)
    if (n != 3).any():
        raise ValueError(f"{obj.name}: triangule antes (pintura.triangular)")
    t = np.empty(len(me.polygons) * 3, np.int64)
    me.polygons.foreach_get("vertices", t)
    return v, t.reshape(-1, 3)


BLOQUEAR, FORCAR = 2, 1  # pintura de suporte: 1 = forçar suporte, 2 = bloquear suporte


def exportar_3mf(obj, cores, caminho, centro_mesa=(90.0, 90.0), nome=None, suportes=None):
    """Um objeto pintado num 3MF (ver exportar_3mf_varios para vários)."""
    return exportar_3mf_varios([(obj, cores, suportes, nome or obj.name)], caminho, centro_mesa)


def exportar_3mf_varios(itens, caminho, centro_mesa=(90.0, 90.0)):
    """Vários objetos pintados num 3MF, nas posições relativas atuais (o conjunto é centrado
    em `centro_mesa` e apoiado em z = 0). `itens`: lista de (obj, cores, suportes|None, nome).
    Serve para a mesa de apresentação (figura montada) ou peças que imprimem juntas."""
    dados = []
    for obj, cores, suportes, nome in itens:
        v, t = arrays_mundo(obj)
        cores = np.asarray(cores)
        if len(cores) != len(t):
            raise ValueError(f"{nome}: cores tem {len(cores)} itens, a malha tem {len(t)} triângulos")
        sup_ = np.zeros(len(t), np.int32) if suportes is None else np.asarray(suportes)
        dados.append((v, t, cores, sup_, nome))
    tudo = np.vstack([d[0] for d in dados])
    desloc = np.array([centro_mesa[0] - (tudo[:, 0].min() + tudo[:, 0].max()) / 2,
                       centro_mesa[1] - (tudo[:, 1].min() + tudo[:, 1].max()) / 2,
                       -tudo[:, 2].min()])
    sup_cod = {0: "", FORCAR: ' paint_supports="4"', BLOQUEAR: ' paint_supports="8"'}
    objetos = []
    for i, (v, t, cores, sup_, nome) in enumerate(dados, 1):
        v = v + desloc
        codigos = {c: codigo(int(c)) for c in np.unique(cores)}
        linhas_v = "\n".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in v)
        linhas_t = "\n".join(
            f'<triangle v1="{a}" v2="{b}" v3="{c}"' + (f' paint_color="{codigos[k]}"' if codigos[k] else "")
            + sup_cod[int(s_)] + "/>"
            for (a, b, c), k, s_ in zip(t, cores, sup_))
        objetos.append(f'<object id="{i}" name="{nome}" type="model">\n<mesh>\n<vertices>\n{linhas_v}\n'
                       f'</vertices>\n<triangles>\n{linhas_t}\n</triangles>\n</mesh>\n</object>')
    itens_build = "\n".join(f'<item objectid="{i}"/>' for i in range(1, len(dados) + 1))
    modelo = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
        '<resources>\n' + "\n".join(objetos) + '\n</resources>\n'
        f'<build>\n{itens_build}\n</build>\n</model>\n')
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _TIPOS)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("3D/3dmodel.model", modelo)
    return caminho
