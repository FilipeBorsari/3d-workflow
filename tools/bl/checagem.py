"""Checagem de imprimibilidade: medidas, malha fechada, mesa, overhangs, ilhas,
autointerseção e espessura de parede."""
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import geometry
from mathutils.bvhtree import BVHTree

from . import RAIZ

CONFIG = json.loads((RAIZ / "config" / "impressora.json").read_text())


def _bmesh_mundo(obj):
    dep = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    bm.from_object(obj, dep)
    bm.transform(obj.matrix_world)
    # Booleanas devolvem n-gonos côncavos; triangular evita falsos positivos nos testes.
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def _nao_manifold_soldado(bm, distancia=1e-4):
    """Arestas não-manifold depois de soldar vértices coincidentes, como o fatiador faz ao ler
    o STL. Pega "gravatas": duas partes que se tocam só numa aresta ou num ponto, que no Blender
    ficam com vértices duplicados e passam como malha fechada."""
    copia = bm.copy()
    bmesh.ops.remove_doubles(copia, verts=copia.verts[:], dist=distancia)
    ruins = sum(1 for e in copia.edges if len(e.link_faces) != 2)
    copia.free()
    return ruins


def _ilhas_z_min(bm):
    """Z mínimo de cada parte conectada da malha (union-find pelos vértices)."""
    bm.verts.index_update()
    pai = list(range(len(bm.verts)))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    for e in bm.edges:
        a, b = raiz(e.verts[0].index), raiz(e.verts[1].index)
        if a != b:
            pai[a] = b
    z_min = {}
    for v in bm.verts:
        r = raiz(v.index)
        z_min[r] = min(z_min.get(r, v.co.z), v.co.z)
    return list(z_min.values())


PENETRACAO_MIN_MM = 0.05  # abaixo disso é ruído numérico de booleana, irrelevante para o fatiador


def _triangulo_bom(face):
    """Descarta lascas: área pequena demais para o tamanho da maior aresta."""
    maior = max(e.calc_length() for e in face.edges)
    return maior > 0 and face.calc_area() / (maior * maior) > 1e-3


def _distancia_borda(ponto, face):
    cos = [v.co for v in face.verts]
    menor = float("inf")
    for k in range(len(cos)):
        a, b = cos[k], cos[(k + 1) % len(cos)]
        ab = b - a
        t = max(0.0, min(1.0, (ponto - a).dot(ab) / ab.length_squared)) if ab.length_squared else 0.0
        menor = min(menor, (a + ab * t - ponto).length)
    return menor


def _aresta_fura_face(a, b, face, eps=PENETRACAO_MIN_MM):
    """True se o segmento a-b atravessa a face (triângulo) com folga > eps de todas as bordas."""
    direcao = b - a
    comprimento = direcao.length
    if comprimento < 2 * eps:
        return False
    direcao /= comprimento
    cos = [v.co for v in face.verts]
    ponto = geometry.intersect_ray_tri(cos[0], cos[1], cos[2], direcao, a, True)
    return (ponto is not None and eps < (ponto - a).length < comprimento - eps
            and _distancia_borda(ponto, face) > eps)


def _autointersecoes(bm, arvore, limite_pares=200_000):
    """Pares de triângulos que realmente se cruzam (aresta de um fura o outro a mais de
    PENETRACAO_MIN_MM das bordas).

    O BVH acusa também faces que só se tocam, e booleanas deixam lascas com cruzamentos
    de centésimos de mm que o fatiador ignora. Cada candidato é confirmado com teste
    aresta x triângulo, sem lascas. None se houver candidatos demais.
    Espera bmesh triangulado (_bmesh_mundo já triangula).
    """
    bm.faces.ensure_lookup_table()
    candidatos = [(i, j) for i, j in arvore.overlap(arvore) if i < j]
    if len(candidatos) > limite_pares:
        return None
    total = 0
    for i, j in candidatos:
        fi, fj = bm.faces[i], bm.faces[j]
        if not {v.index for v in fi.verts}.isdisjoint(v.index for v in fj.verts):
            continue
        if not (_triangulo_bom(fi) and _triangulo_bom(fj)):
            continue
        if any(_aresta_fura_face(e.verts[0].co, e.verts[1].co, fj) for e in fi.edges) or \
           any(_aresta_fura_face(e.verts[0].co, e.verts[1].co, fi) for e in fj.edges):
            total += 1
    return total


def _espessuras(bm, arvore, amostras=4000):
    """Espessura local: raio de cada face para dentro até sair do sólido. Lista (mm, área)."""
    faces = [f for f in bm.faces if f.calc_area() > 1e-3]  # ignora lascas de booleana
    medidas = []
    for f in faces[::max(1, len(faces) // amostras)]:
        direcao = -f.normal
        local, normal, _, distancia = arvore.ray_cast(f.calc_center_median() + direcao * 1e-3, direcao)
        # Só conta quando o raio sai do sólido (face de trás) longe da origem: toques
        # numéricos com faces vizinhas dão distância ~0 e não são parede.
        if local is not None and normal.dot(direcao) > 0 and distancia > 0.02:
            medidas.append((distancia + 1e-3, f.calc_area()))
    return medidas


def _percentil(medidas, p):
    total = sum(a for _, a in medidas)
    acumulado = 0.0
    for valor, area in sorted(medidas):
        acumulado += area
        if acumulado >= total * p:
            return valor
    return medidas[-1][0] if medidas else None


def defeitos(obj):
    """Checagem rápida para validar booleanas: (arestas não-manifold, autointerseções)."""
    bm = _bmesh_mundo(obj)
    if not bm.faces:
        bm.free()
        return None
    abertas = sum(1 for e in bm.edges if not e.is_manifold)
    cruzadas = _autointersecoes(bm, BVHTree.FromBMesh(bm)) or 0
    bm.free()
    return abertas, cruzadas


def relatorio_objeto(obj):
    bm = _bmesh_mundo(obj)
    if not bm.verts:
        bm.free()
        return {"nome": obj.name, "erro": "objeto sem geometria"}
    xs, ys, zs = zip(*(v.co[:] for v in bm.verts))
    dims = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]
    mesa = CONFIG["volume_util_mm"]
    margem = CONFIG["margem_mesa_mm"]
    limite_overhang = math.cos(math.radians(90 - CONFIG["projeto"]["overhang_max_graus"]))
    z0 = min(zs)

    arestas_abertas = sum(1 for e in bm.edges if not e.is_manifold)
    soldado = _nao_manifold_soldado(bm)
    area_contato = sum(f.calc_area() for f in bm.faces
                       if f.normal.z < -0.99 and all(abs(v.co.z - z0) < 0.05 for v in f.verts))
    area_overhang = sum(f.calc_area() for f in bm.faces
                        if f.normal.z < -limite_overhang and min(v.co.z for v in f.verts) > z0 + 0.3)
    fechada = arestas_abertas == 0 and soldado == 0
    regras = CONFIG["projeto"]
    arvore = BVHTree.FromBMesh(bm)
    ilhas = _ilhas_z_min(bm)
    espessuras = _espessuras(bm, arvore)
    area_amostrada = sum(a for _, a in espessuras) or 1.0
    rel = {
        "nome": obj.name,
        "dimensoes_mm": [round(d, 2) for d in dims],
        "z_min_mm": round(z0, 3),
        "triangulos": sum(len(f.verts) - 2 for f in bm.faces),
        "malha_fechada": fechada,
        "arestas_nao_manifold": arestas_abertas,
        "nao_manifold_apos_soldar": soldado,
        "bordas_abertas": sum(1 for e in bm.edges if len(e.link_faces) == 1),
        "arestas_com_3_ou_mais_faces": sum(1 for e in bm.edges if len(e.link_faces) > 2),
        "faces_degeneradas": sum(1 for f in bm.faces if f.calc_area() < 1e-8),
        "vertices_soltos": sum(1 for v in bm.verts if not v.link_faces),
        "autointersecoes": _autointersecoes(bm, arvore),
        "ilhas": len(ilhas),
        "ilhas_flutuando": sum(1 for z in ilhas if z > z0 + 0.05),
        "volume_cm3": round(bm.calc_volume(signed=True) / 1000, 2) if fechada else None,
        "espessura_min_mm": round(min(e for e, _ in espessuras), 2) if espessuras else None,
        "espessura_p5_mm": round(_percentil(espessuras, 0.05), 2) if espessuras else None,
        "area_abaixo_parede_min_pct": round(100 * sum(a for e, a in espessuras
                                                      if e < regras["parede_minima_mm"]) / area_amostrada, 1),
        "area_abaixo_detalhe_min_pct": round(100 * sum(a for e, a in espessuras
                                                       if e < regras["detalhe_minimo_mm"]) / area_amostrada, 1),
        "area_contato_mesa_mm2": round(area_contato, 1),
        "area_overhang_mm2": round(area_overhang, 1),
        "cabe_na_mesa": dims[0] <= mesa["x"] - 2 * margem and dims[1] <= mesa["y"] - 2 * margem
                        and dims[2] <= mesa["z"],
    }
    bm.free()

    avisos = []
    if not rel["malha_fechada"]:
        avisos.append(f"malha aberta / não-manifold ({rel['bordas_abertas']} bordas abertas, "
                      f"{rel['arestas_com_3_ou_mais_faces']} arestas com 3+ faces): o fatiador pode "
                      "falhar, pular camadas ou deixar buracos")
    if rel["nao_manifold_apos_soldar"] and not rel["arestas_nao_manifold"]:
        avisos.append(f"{rel['nao_manifold_apos_soldar']} arestas viram não-manifold ao soldar vértices "
                      "coincidentes (partes se tocando só numa aresta/ponto): o Bambu acusa 'manifold = no'. "
                      "Una um preenchimento pequeno no ponto ou afaste as partes")
    if rel["autointersecoes"]:
        avisos.append(f"{rel['autointersecoes']} pares de faces se cruzando: una as partes com booleana "
                      "UNION (malha.booleana) em vez de malha.juntar")
    if rel["ilhas_flutuando"]:
        avisos.append(f"{rel['ilhas_flutuando']} parte(s) solta(s) acima da base: vão imprimir no ar")
    elif rel["ilhas"] > 1:
        avisos.append(f"{rel['ilhas']} partes separadas no mesmo objeto: confirme se é intencional")
    if rel["faces_degeneradas"]:
        avisos.append(f"{rel['faces_degeneradas']} faces de área zero: rode malha.limpar(obj)")
    if rel["area_abaixo_detalhe_min_pct"] > 0.5:
        avisos.append(f"{rel['area_abaixo_detalhe_min_pct']}% da superfície com espessura < "
                      f"{regras['detalhe_minimo_mm']} mm: detalhe pode sumir no fatiamento")
    if rel["area_abaixo_parede_min_pct"] > 5:
        avisos.append(f"{rel['area_abaixo_parede_min_pct']}% da superfície com espessura < "
                      f"{regras['parede_minima_mm']} mm: parede fraca (menos de 3 linhas)")
    if rel["volume_cm3"] is not None and rel["volume_cm3"] < 0:
        avisos.append("volume negativo: normais invertidas")
    if abs(z0) > 0.01:
        avisos.append(f"peça não apoiada em Z=0 (z_min={z0:.3f})")
    if not rel["cabe_na_mesa"]:
        avisos.append(f"não cabe no volume útil {mesa['x']}x{mesa['y']}x{mesa['z']} mm (margem {margem} mm)")
    if rel["area_contato_mesa_mm2"] < 50:
        avisos.append("pouca área de contato com a mesa: risco de soltar (considere brim ou reorientar)")
    if rel["area_overhang_mm2"] > 0:
        avisos.append("há overhangs acima do limite: provável necessidade de suporte")
    rel["avisos"] = avisos
    return rel


def relatorio(objs=None, caminho=None):
    """Relatório JSON dos objetos (padrão: todas as malhas visíveis). Imprime e salva."""
    objs = objs or [o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()]
    dados = {"impressora": CONFIG["impressora"], "objetos": [relatorio_objeto(o) for o in objs]}
    texto = json.dumps(dados, indent=2, ensure_ascii=False)
    print("RELATORIO_JSON_INICIO\n" + texto + "\nRELATORIO_JSON_FIM")
    if caminho:
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        Path(caminho).write_text(texto)
    return dados
