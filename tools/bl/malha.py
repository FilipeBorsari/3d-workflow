"""Operações de malha comuns em peças para impressão."""
import bmesh
import bpy


def selecionar(objs, ativo=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ativo or objs[0]


def aplicar_modificadores(obj):
    """Aplica todos os modificadores (pilha avaliada) e mantém o objeto."""
    dep = bpy.context.evaluated_depsgraph_get()
    malha = bpy.data.meshes.new_from_object(obj.evaluated_get(dep))
    obj.modifiers.clear()
    antiga, obj.data = obj.data, malha
    if antiga.users == 0:
        bpy.data.meshes.remove(antiga)
    return obj


def aplicar_transformacoes(obj, posicao=False):
    """Grava rotação e escala (e a posição, se posicao=True) nos vértices."""
    selecionar([obj])
    bpy.ops.object.transform_apply(location=posicao, rotation=True, scale=True)
    return obj


SOLVERS = ("MANIFOLD", "FLOAT", "EXACT")


def _vertices_dentro(alvo, ferramenta, amostras=3000, margem=0.05):
    """Quantos vértices do alvo (amostra dos que caem na caixa da ferramenta) estão dentro da
    ferramenta, longe da superfície dela. Numa DIFFERENCE certa, nenhum."""
    import random

    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    dep = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    bm.from_object(ferramenta, dep)
    bm.transform(ferramenta.matrix_world)
    if not bm.verts:
        bm.free()
        return 0
    lo = np.array([min(v.co[i] for v in bm.verts) for i in range(3)])
    hi = np.array([max(v.co[i] for v in bm.verts) for i in range(3)])
    arvore = BVHTree.FromBMesh(bm)
    bm.free()
    co = np.empty(len(alvo.data.vertices) * 3)
    alvo.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    m = np.array(alvo.matrix_world)
    co = co @ m[:3, :3].T + m[:3, 3]
    candidatos = np.nonzero(np.all((co > lo) & (co < hi), axis=1))[0].tolist()
    if len(candidatos) > amostras:
        candidatos = random.Random(1).sample(candidatos, amostras)
    # 3 direções e voto da maioria: raio que passa rente numa aresta conta errado
    direcoes = [Vector(d).normalized() for d in ((0.5773, 0.5774, 0.5776), (-0.31, 0.8, 0.51), (0.72, -0.41, 0.56))]
    dentro = 0
    for i in candidatos:
        p = Vector(co[i])
        perto = arvore.find_nearest(p)
        if perto[0] is not None and perto[3] < margem:
            continue  # está na superfície do corte
        votos = 0
        for direcao in direcoes:
            cruzou, origem = 0, p
            for _ in range(60):
                achou = arvore.ray_cast(origem, direcao)
                if achou[0] is None:
                    break
                cruzou += 1
                origem = achou[0] + direcao * 1e-5
            votos += cruzou % 2
        dentro += votos >= 2
    # poucos casos isolados são rente à superfície (ruído do teste); falha de verdade deixa muitos
    return dentro if candidatos and dentro > 0.01 * len(candidatos) else 0


def booleana(alvo, ferramenta, operacao="DIFFERENCE", apagar_ferramenta=True, solver="AUTO"):
    """operacao: DIFFERENCE, UNION ou INTERSECT.

    solver="AUTO" tenta MANIFOLD, FLOAT e EXACT, nessa ordem, e fica com o primeiro
    resultado sem defeito (arestas abertas ou triângulos cruzados). Nos testes nenhum
    solver acertou todos os casos: MANIFOLD cruzou triângulos ao unir logo em cilindro,
    EXACT abriu arestas ao unir logo plano, FLOAT acertou os dois mas falha em faces
    coplanares. Passe um solver específico só se souber o que está fazendo.
    """
    from . import checagem

    if alvo.modifiers:
        aplicar_modificadores(alvo)  # congela pendentes; cada tentativa parte da mesma malha
    original = alvo.data
    melhor = None  # (total de defeitos, solver, malha, defeitos)
    for nome in (SOLVERS if solver == "AUTO" else (solver,)):
        alvo.data = original.copy()
        mod = alvo.modifiers.new("bool", "BOOLEAN")
        mod.operation = operacao
        mod.solver = nome
        mod.object = ferramenta
        aplicar_modificadores(alvo)
        resultado = alvo.data
        achados = checagem.defeitos(alvo) if resultado.polygons else None
        total = sum(achados) if achados is not None else float("inf")
        if operacao == "DIFFERENCE" and achados is not None:
            # Já aconteceu de um solver devolver a malha sem corte e sem defeito: confere se
            # sobrou vértice do alvo dentro da ferramenta.
            sobra = _vertices_dentro(alvo, ferramenta)
            if sobra:
                achados = (*achados, sobra)
                total += sobra
        alvo.data = original
        if melhor is None or total < melhor[0]:
            if melhor:
                bpy.data.meshes.remove(melhor[2])
            melhor = (total, nome, resultado, achados)
        else:
            bpy.data.meshes.remove(resultado)
        if total == 0:
            break
    total, nome, resultado, achados = melhor
    alvo.data = resultado
    if original.users == 0:
        bpy.data.meshes.remove(original)
    if total:
        print(f"[malha.booleana] '{alvo.name}' {operacao} '{ferramenta.name}': nenhum solver saiu limpo; "
              f"usando {nome} com defeitos (arestas abertas, cruzamentos[, vértices não cortados]) = {achados}")
    if apagar_ferramenta:
        bpy.data.objects.remove(ferramenta, do_unlink=True)
    return alvo


def juntar(objs, nome=None):
    selecionar(objs)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    if nome:
        obj.name = nome
    return obj


def apoiar_na_mesa(obj, centralizar=True):
    """Move o objeto para Z mínimo = 0 e, opcionalmente, centraliza em XY."""
    dep = bpy.context.evaluated_depsgraph_get()
    avaliado = obj.evaluated_get(dep)
    cantos = [obj.matrix_world @ v.co for v in avaliado.data.vertices]
    if not cantos:
        return obj
    obj.location.z -= min(c.z for c in cantos)
    if centralizar:
        obj.location.x -= (min(c.x for c in cantos) + max(c.x for c in cantos)) / 2
        obj.location.y -= (min(c.y for c in cantos) + max(c.y for c in cantos)) / 2
    return obj


def limpar(obj, distancia=0.001):
    """Funde vértices duplicados e recalcula normais para fora."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distancia)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def fechar_pincamentos(obj, raio=0.4, tentativas=3):
    """Partes que se tocam só numa aresta/ponto ("gravata") passam como malha fechada no
    Blender, mas viram arestas não-manifold quando o fatiador solda os vértices do STL (o Bambu
    acusa "manifold = no"). Une uma esferinha em cada ponto até sumirem.
    (Veio de projetos/caneca-jo-spinola/modelo_v2.py.)"""
    import bpy as _bpy
    for _ in range(tentativas):
        # triangula de vez (como a exportação): n-gonos de booleana podem esconder o defeito
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(obj.data)
        bm.free()
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
        pontos = [(e.verts[0].co + e.verts[1].co) / 2 for e in bm.edges if len(e.link_faces) != 2]
        bm.free()
        if not pontos:
            return obj
        print(f"[{obj.name}] {len(pontos)} pinçamento(s) fechado(s) com esferas de {raio} mm")
        esferas = []
        for ponto in pontos:
            b = bmesh.new()
            bmesh.ops.create_icosphere(b, subdivisions=2, radius=raio)
            bmesh.ops.translate(b, verts=b.verts[:], vec=ponto)
            dados = _bpy.data.meshes.new("esfera")
            b.to_mesh(dados)
            b.free()
            esfera = _bpy.data.objects.new("esfera", dados)
            _bpy.context.scene.collection.objects.link(esfera)
            esferas.append(esfera)
        booleana(obj, juntar(esferas, "esferas"), "UNION")
        limpar(obj, distancia=1e-4)
    return obj


def manter_maior_ilha(obj):
    """Apaga todas as partes soltas, menos a maior (em vértices). Remesh voxel e decimação
    deixam fragmentos de poucos vértices, às vezes com bordas abertas."""
    import numpy as np

    me = obj.data
    n = len(me.vertices)
    arestas = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", arestas)
    a, b = arestas[0::2], arestas[1::2]
    rotulo = np.arange(n)
    while True:  # propaga o menor rótulo pelas arestas até estabilizar
        menor = np.minimum(rotulo[a], rotulo[b])
        novo = rotulo.copy()
        np.minimum.at(novo, a, menor)
        np.minimum.at(novo, b, menor)
        novo = novo[novo]
        if (novo == rotulo).all():
            break
        rotulo = novo
    ids, contagem = np.unique(rotulo, return_counts=True)
    if len(ids) == 1:
        return obj
    fora = rotulo != ids[np.argmax(contagem)]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(fora)[0]], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    print(f"[{obj.name}] {len(ids) - 1} ilha(s) solta(s) apagada(s), {np.count_nonzero(fora)} vértices")
    return obj
