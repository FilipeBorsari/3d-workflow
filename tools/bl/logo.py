"""SVG -> malha em relevo (logos, textos, silhuetas).

Fluxo: imagem -> tools/imagem_para_svg.py -> SVG -> svg_para_malha() -> peça/booleana.
"""
import math

import bmesh
import bpy
from mathutils import Matrix

from . import malha


def svg_para_malha(caminho_svg, largura_mm, altura_mm, nome="logo", resolucao_curva=4):
    """Importa o SVG, extruda e devolve UM objeto malha.

    largura_mm: largura final em X. altura_mm: espessura do relevo em Z.
    O objeto sai centrado em XY com a base em Z=0.
    """
    antes = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(caminho_svg))
    curvas = [o for o in bpy.data.objects if o not in antes and o.type == "CURVE"]
    if not curvas:
        raise RuntimeError(f"SVG sem curvas: {caminho_svg}")

    for c in curvas:
        c.data.dimensions = "2D"
        c.data.fill_mode = "BOTH"
        c.data.resolution_u = resolucao_curva
        c.data.extrude = 0.0
    obj = malha.juntar(curvas, nome) if len(curvas) > 1 else curvas[0]
    obj.name = nome

    # Curva 2D não aceita aplicar transformações: extruda, converte e só então escala.
    obj.data.extrude = 0.5
    malha.selecionar([obj])
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.view_layer.objects.active
    if obj.dimensions.x <= 0 or obj.dimensions.z <= 0:
        raise RuntimeError("SVG gerou malha vazia ou plana")
    fator = largura_mm / obj.dimensions.x
    obj.scale = (obj.scale.x * fator, obj.scale.y * fator, obj.scale.z * altura_mm / obj.dimensions.z)
    malha.aplicar_transformacoes(obj)
    malha.limpar(obj)
    malha.apoiar_na_mesa(obj)
    malha.aplicar_transformacoes(obj, posicao=True)

    # Colecoes vazias criadas pelo importador
    for col in list(bpy.data.collections):
        if not col.objects and not col.children:
            bpy.data.collections.remove(col)
    return obj


def enrolar_em_cilindro(obj, raio, z_centro, afundar=0.4, passo_mm=1.0, angulo_centro=-math.pi / 2):
    """Enrola um relevo plano (saída de svg_para_malha/texto: XY = desenho, Z = altura)
    na parede externa de um cilindro de eixo Z.

    - X do desenho vira arco (comprimento preservado), Y vira altura na parede.
    - Z do desenho vira direção radial: base fica `afundar` mm dentro da parede para a
      booleana UNION não ter faces coincidentes. Para gravação (DIFFERENCE), use afundar
      maior que a profundidade desejada ou inverta o relevo.
    - passo_mm: fatia o desenho em X antes de curvar (menor = mais fiel à curvatura).
    - angulo_centro: onde fica o centro do desenho. -pi/2 = lado -Y (frente nas previews).
    """
    malha.aplicar_transformacoes(obj)
    dados = obj.data
    bm = bmesh.new()
    bm.from_mesh(dados)
    bm.transform(obj.matrix_world)
    xs = [v.co.x for v in bm.verts]
    x = min(xs) + passo_mm
    while x < max(xs):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
        x += passo_mm
    # Triangula antes de curvar: polígono plano curvado fica não-planar, e n-gono
    # não-planar triangulado depois gera faces dobradas (autointerseção no STL).
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for v in bm.verts:
        teta = angulo_centro + v.co.x / raio
        r = raio - afundar + v.co.z
        v.co = (r * math.cos(teta), r * math.sin(teta), z_centro + v.co.y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(dados)
    bm.free()
    obj.matrix_world = Matrix.Identity(4)
    dados.update()
    return obj


def enrolar_em_revolucao(obj, raio_de_z, z_centro, afundar=0.4, passo_mm=1.0, angulo_centro=-math.pi / 2):
    """Como `enrolar_em_cilindro`, mas numa superfície de revolução de raio variável
    (caneca com barriga, vaso). `raio_de_z(z)` devolve o raio externo na altura z (mm).

    Fatia o desenho em X e em Y (o raio muda com a altura) e preserva o comprimento de
    arco em cada altura. O relevo sai na direção radial; em paredes com até ~30° de
    inclinação a diferença para a normal é desprezível (< 5% da altura do relevo).
    """
    malha.aplicar_transformacoes(obj)
    dados = obj.data
    bm = bmesh.new()
    bm.from_mesh(dados)
    bm.transform(obj.matrix_world)
    for eixo, normal in ((0, (1, 0, 0)), (1, (0, 1, 0))):
        valores = [v.co[eixo] for v in bm.verts]
        c = min(valores) + passo_mm
        while c < max(valores):
            ponto = [0.0, 0.0, 0.0]
            ponto[eixo] = c
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=ponto, plane_no=normal)
            c += passo_mm
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for v in bm.verts:
        z = z_centro + v.co.y
        raio = raio_de_z(z)
        teta = angulo_centro + v.co.x / raio
        r = raio - afundar + v.co.z
        v.co = (r * math.cos(teta), r * math.sin(teta), z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(dados)
    bm.free()
    obj.matrix_world = Matrix.Identity(4)
    dados.update()
    return obj
