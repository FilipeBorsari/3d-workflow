"""Folha de cotas: vistas ortográficas (frente, lado, topo) renderizadas no Blender e cotas
desenhadas por cima com Pillow (Python do sistema, tools/desenhar_cotas.py).

Uso num script bpy do projeto (ver projetos/*/cotas.py):

    from bl import cotas
    v = cotas.vista(objs, "frente", pasta / "frente.png", titulo="Explodido - frente")
    v["cotas"] = [cotas.linha((-50, 0, 0), (50, 0, 0), "100", lado=-1, dist=12),
                  cotas.nota((0, -70, 3), "bica 20 x 3", dx=30, dy=-20)]
    cotas.folha(pasta, "Escorredor", [v, ...], notas=["medidas em mm"])

Pontos em coordenadas do mundo (mm). `lado` escolhe de que lado da reta a cota fica e
`dist` é o afastamento em mm. A vista "lado" olha de +X para -X (Y para a direita).
"""
import json
import math
import subprocess
from pathlib import Path

import bpy
from mathutils import Vector

from . import formas, malha, preview

# rotação da câmera, eixos (u, v) do mundo na imagem e direção de onde a câmera olha
DIRECOES = {
    "frente": ((math.pi / 2, 0, 0), (0, 2), Vector((0, -1, 0))),
    "lado": ((math.pi / 2, 0, math.pi / 2), (1, 2), Vector((1, 0, 0))),
    "topo": ((0, 0, 0), (0, 1), Vector((0, 0, 1))),
    "iso": (None, (0, 2), Vector((1, -1, 0.8)).normalized()),   # só imagem, sem cotas
}
DESENHAR = Path(__file__).resolve().parents[1] / "desenhar_cotas.py"


def fmt(x):
    """Número em mm com vírgula, sem casa decimal quando inteiro: 141.97 -> '142'."""
    return f"{x:.1f}".replace(".", ",").removesuffix(",0")


def copia(obj, desloc=(0, 0, 0), cor=None):
    """Cópia independente do objeto, deslocada (mm) e com transformação aplicada."""
    c = obj.copy()
    c.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(c)
    c.location = Vector(c.location) + Vector(desloc)
    malha.aplicar_transformacoes(c, posicao=True)
    c.color = cor or obj.color
    return c


def apagar(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def corte(objs, eixo, valor, manter="-", tamanho=1000.0):
    """Metade de cada objeto (INTERSECT com caixa grande): eixo 0/1/2, plano em `valor`,
    mantém o lado "-" ou "+". Devolve cópias cortadas com as mesmas cores."""
    saida = []
    for o in objs:
        c = copia(o)
        caixa = formas.caixa(tamanho, tamanho, tamanho, nome="meia")
        pos = [0.0, 0.0, -tamanho / 2]
        pos[eixo] = valor + (tamanho / 2 if manter == "+" else -tamanho / 2)
        if eixo == 2:
            pos[2] = valor - tamanho if manter == "-" else valor
        caixa.location = pos
        malha.aplicar_transformacoes(caixa, posicao=True)
        saida.append(malha.booleana(c, caixa, "INTERSECT"))
        saida[-1].color = o.color
    return saida


def linha(a, b, texto, lado=1, dist=10.0):
    return {"tipo": "linha", "a": list(a), "b": list(b), "texto": texto, "lado": lado, "dist": dist}


def nota(p, texto, dx=20.0, dy=20.0):
    return {"tipo": "nota", "p": list(p), "texto": texto, "dx": dx, "dy": dy}


def vista(objs, direcao, arquivo, titulo="", resolucao=1400, folga=0.32, regiao=None):
    """Renderiza uma vista ortográfica dos objetos (cores de `obj.color`) e devolve os dados
    para converter mm em pixels. regiao=((x0, y0, z0), (x1, y1, z1)) enquadra só esse trecho
    (detalhe ampliado)."""
    cena = bpy.context.scene
    rot, (i, j), olhar = DIRECOES[direcao]
    minimo, maximo = preview._limites(objs)
    if regiao:
        minimo, maximo = Vector(regiao[0]), Vector(regiao[1])
    centro = (minimo + maximo) / 2
    tamanho = max(maximo[i] - minimo[i], maximo[j] - minimo[j]) * (1 + 2 * folga)
    if rot is None:
        rot = (-olhar).to_track_quat("-Z", "Y").to_euler()
        tamanho = (maximo - minimo).length * 1.05
    ocultos = [o for o in cena.objects if o not in objs and o.type == "MESH" and not o.hide_render]
    for o in ocultos:
        o.hide_render = True
    cam_dados = bpy.data.cameras.new("cotas_cam")
    cam_dados.type = "ORTHO"
    cam_dados.ortho_scale = tamanho
    cam_dados.clip_end = 100000
    cam = bpy.data.objects.new("cotas_cam", cam_dados)
    cena.collection.objects.link(cam)
    cam.location = centro + olhar * 3000
    cam.rotation_euler = rot
    antiga = cena.camera
    cena.camera = cam
    preview._configurar_render(cena, resolucao)
    cena.render.use_stamp = False
    cena.display.shading.background_color = (1, 1, 1)
    vista_cor = cena.view_settings.view_transform
    cena.view_settings.view_transform = "Standard"   # AgX/Filmic deixam o fundo branco cinza
    cena.render.filepath = str(arquivo)
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        cena.camera = antiga
        cena.view_settings.view_transform = vista_cor
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.cameras.remove(cam_dados)
        for o in ocultos:
            o.hide_render = False
    return {"arquivo": str(arquivo), "titulo": titulo, "eixos": [i, j],
            "centro": [centro[i], centro[j]], "px_mm": resolucao / tamanho,
            "resolucao": resolucao, "cotas": []}


def folha(pasta, titulo, vistas, notas=(), nome="cotas.png"):
    """Grava o JSON e chama o desenhista (Python do sistema, com Pillow)."""
    pasta = Path(pasta)
    dados = {"titulo": titulo, "vistas": vistas, "notas": list(notas), "saida": str(pasta / nome)}
    caminho = pasta / (Path(nome).stem + ".json")
    caminho.write_text(json.dumps(dados, indent=1, ensure_ascii=False))
    subprocess.run(["python3", str(DESENHAR), str(caminho)], check=True)
    return pasta / nome
