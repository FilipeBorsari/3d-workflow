"""Formas base em mm, já apoiadas em Z=0 (salvo indicação).

Toda forma sai com transformação zerada (posição gravada nos vértices): mover com
`obj.location.x += 10` desloca a peça 10 mm a partir de onde ela foi criada.
"""
import math

import bmesh
import bpy

from . import malha


def _ligar(obj):
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


def caixa(largura, profundidade, altura, chanfro=0.0, nome="caixa"):
    """Caixa centrada em XY, base em Z=0. chanfro > 0 chanfra todas as arestas."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.active_object
    obj.name = nome
    obj.scale = (largura, profundidade, altura)
    malha.aplicar_transformacoes(obj)
    obj.location.z = altura / 2
    malha.aplicar_transformacoes(obj, posicao=True)
    if chanfro:
        mod = obj.modifiers.new("chanfro", "BEVEL")
        mod.width = chanfro
        mod.segments = 1
        malha.aplicar_modificadores(obj)
    return obj


def cilindro(raio, altura, vertices=96, z0=0.0, nome="cilindro"):
    """Cilindro no eixo Z, de z0 até z0+altura."""
    bpy.ops.mesh.primitive_cylinder_add(radius=raio, depth=altura, vertices=vertices,
                                        location=(0, 0, z0 + altura / 2))
    obj = bpy.context.active_object
    obj.name = nome
    return malha.aplicar_transformacoes(obj, posicao=True)


def tubo(raio_externo, raio_interno, altura, vertices=96, nome="tubo"):
    externo = cilindro(raio_externo, altura, vertices, nome=nome)
    furo = cilindro(raio_interno, altura + 2, vertices, z0=-1)
    return malha.booleana(externo, furo, "DIFFERENCE")


def revolucao(perfil_rz, passos=128, nome="revolucao"):
    """Sólido de revolução em torno de Z.

    perfil_rz: lista de (raio, z) percorrendo a seção do eixo para fora e de volta ao eixo,
    sem repetir o primeiro ponto. Ex. copo: [(0,0), (R,0), (R,H), (R-e,H), (R-e,f), (0,f)].
    Pontos com raio 0 ficam sobre o eixo e fecham o sólido.
    """
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z)) for r, z in perfil_rz]
    arestas = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + arestas, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.tau, steps=passos, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    dados = bpy.data.meshes.new(nome)
    bm.to_mesh(dados)
    bm.free()
    return _ligar(bpy.data.objects.new(nome, dados))


def rosca_externa(raio_raiz, profundidade, passo, z_inicio, voltas, base=None, crista=0.4,
                  embutir=0.3, passos_volta=96, nome="rosca"):
    """Filete helicoidal (sentido anti-horário subindo = rosca direita) para unir a um cilindro.

    Perfil trapezoidal: `base` (padrão 0,9 x passo) na raiz, `crista` no topo, com `embutir` mm
    para dentro do raio da raiz (sobreposição para a UNION). z_inicio = centro do filete na
    ponta de baixo. Corte o excesso acima do topo do colar com uma DIFFERENCE.
    """
    base = base or 0.9 * passo
    r0, r1 = raio_raiz - embutir, raio_raiz + profundidade
    perfil = [(r0, -base / 2), (raio_raiz, -base / 2), (r1, -crista / 2), (r1, crista / 2),
              (raio_raiz, base / 2), (r0, base / 2)]
    bm = bmesh.new()
    aneis = []
    for i in range(round(voltas * passos_volta) + 1):
        ang = math.tau * i / passos_volta
        zc = z_inicio + passo * i / passos_volta
        c, s = math.cos(ang), math.sin(ang)
        aneis.append([bm.verts.new((r * c, r * s, zc + dz)) for r, dz in perfil])
    n = len(perfil)
    for a, b in zip(aneis, aneis[1:]):
        for j in range(n):
            k = (j + 1) % n
            bm.faces.new((a[j], a[k], b[k], b[j]))
    bm.faces.new(aneis[0])
    bm.faces.new(list(reversed(aneis[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    dados = bpy.data.meshes.new(nome)
    bm.to_mesh(dados)
    bm.free()
    return _ligar(bpy.data.objects.new(nome, dados))


def prisma(pontos, comprimento, eixo="Y", nome="prisma"):
    """Polígono 2D extrudado ao longo de um eixo, centrado nele (de -comprimento/2 a +).

    pontos: lista (a, b) no plano perpendicular ao eixo, sem repetir o primeiro:
    eixo "X" -> (y, z); eixo "Y" -> (x, z); eixo "Z" -> (x, y). Bom para perfis de furo
    em gota, alças, cunhas com 45° e abas.
    """
    def ponto(a, b, t):
        return {"X": (t, a, b), "Y": (a, t, b), "Z": (a, b, t)}[eixo]

    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new(ponto(a, b, -comprimento / 2)) for a, b in pontos])
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(bm, vec=ponto(0, 0, comprimento),
                        verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    dados = bpy.data.meshes.new(nome)
    bm.to_mesh(dados)
    bm.free()
    return _ligar(bpy.data.objects.new(nome, dados))


def texto(conteudo, altura_letra, espessura, fonte=None, nome="texto"):
    """Texto 3D centrado em XY, base em Z=0. altura_letra ~ altura das maiúsculas em mm.

    fonte: caminho de .ttf/.otf (liste com `fc-list`). Padrão: fonte embutida do Blender.
    """
    curva = bpy.data.curves.new(nome, "FONT")
    curva.body = conteudo
    if fonte:
        curva.font = bpy.data.fonts.load(str(fonte))
    curva.size = altura_letra / 0.7  # size do Blender ~ altura total; maiúscula ~70%
    curva.align_x = "CENTER"
    curva.align_y = "CENTER"
    curva.extrude = espessura / 2
    obj = _ligar(bpy.data.objects.new(nome, curva))
    malha.selecionar([obj])
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.view_layer.objects.active
    malha.limpar(obj)
    malha.apoiar_na_mesa(obj)
    return malha.aplicar_transformacoes(obj, posicao=True)


def furo_parafuso(alvo, x, y, altura_peca, d_furo=3.4, d_cabeca=6.2, prof_cabeca=3.2, vertices=48):
    """Furo passante vertical com rebaixo para cabeça (padrão M3) a partir do topo da peça."""
    furo = cilindro(d_furo / 2, altura_peca + 2, vertices, z0=-1, nome="furo")
    cabeca = cilindro(d_cabeca / 2, prof_cabeca + 1, vertices, z0=altura_peca - prof_cabeca, nome="cabeca")
    ferramenta = malha.booleana(furo, cabeca, "UNION")
    ferramenta.location.x += x
    ferramenta.location.y += y
    return malha.booleana(alvo, ferramenta, "DIFFERENCE")
