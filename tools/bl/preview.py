"""Renderização de previews (Workbench) para conferir o modelo sem abrir o Blender.

Gera uma imagem por vista e uma folha 2x2 (`folha.png`) com iso, frente, lado e topo.
"""
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

VISTAS = {
    "iso": Vector((1, -1, 0.8)),
    "frente": Vector((0, -1, 0)),
    "lado": Vector((1, 0, 0)),
    "topo": Vector((0, 0, 1)),
}
CORES = [(0.55, 0.62, 0.78, 1), (0.88, 0.58, 0.35, 1), (0.48, 0.74, 0.52, 1),
         (0.78, 0.52, 0.72, 1), (0.85, 0.8, 0.45, 1), (0.5, 0.75, 0.8, 1)]


def _limites(objs):
    dep = bpy.context.evaluated_depsgraph_get()
    pontos = []
    for o in objs:
        avaliado = o.evaluated_get(dep)
        pontos += [o.matrix_world @ Vector(c) for c in avaliado.bound_box]
    minimo = Vector(tuple(min(p[i] for p in pontos) for i in range(3)))
    maximo = Vector(tuple(max(p[i] for p in pontos) for i in range(3)))
    return minimo, maximo


def _configurar_render(cena, resolucao):
    cena.render.engine = "BLENDER_WORKBENCH"
    cena.render.resolution_x = cena.render.resolution_y = resolucao
    cena.render.resolution_percentage = 100
    cena.render.film_transparent = False
    cena.render.image_settings.file_format = "PNG"
    sombra = cena.display.shading
    sombra.light = "STUDIO"
    sombra.color_type = "OBJECT"
    sombra.show_cavity = True
    sombra.cavity_type = "BOTH"
    sombra.show_object_outline = True
    sombra.background_type = "VIEWPORT"
    sombra.background_color = (0.92, 0.92, 0.92)
    cena.display.shading.show_shadows = False
    # Legenda (vista + escala) gravada na própria imagem
    r = cena.render
    r.use_stamp = True
    for campo in ("date", "time", "render_time", "frame", "frame_range", "memory", "hostname", "camera",
                  "lens", "scene", "marker", "filename", "sequencer_strip"):
        if hasattr(r, f"use_stamp_{campo}"):
            setattr(r, f"use_stamp_{campo}", False)
    r.use_stamp_note = True
    r.stamp_font_size = max(14, resolucao // 30)
    r.stamp_foreground = (0, 0, 0, 1)
    r.stamp_background = (1, 1, 1, 0.85)


def _folha(arquivos, destino):
    imagens = [bpy.data.images.load(str(a)) for a in arquivos]
    w, h = imagens[0].size
    folha = np.zeros((2 * h, 2 * w, 4), dtype=np.float32)
    posicoes = [(1, 0), (1, 1), (0, 0), (0, 1)]  # linhas de baixo para cima (Blender)
    for img, (lin, col) in zip(imagens, posicoes):
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        folha[lin * h:(lin + 1) * h, col * w:(col + 1) * w] = px.reshape(h, w, 4)
    saida = bpy.data.images.new("folha", 2 * w, 2 * h, alpha=True)
    saida.pixels.foreach_set(folha.ravel())
    saida.filepath_raw = str(destino)
    saida.file_format = "PNG"
    saida.save()
    for img in imagens + [saida]:
        bpy.data.images.remove(img)
    return destino


def renderizar(objs=None, pasta="preview", resolucao=600, vistas=tuple(VISTAS), manter_cores=False):
    """Renderiza vistas ortográficas dos objetos. Devolve o caminho da folha 2x2.

    manter_cores=True usa a cor que cada objeto já tem (`obj.color`) em vez da paleta.
    """
    cena = bpy.context.scene
    objs = objs or [o for o in cena.objects if o.type in {"MESH", "CURVE", "FONT"} and o.visible_get()]
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)

    ocultos = [o for o in cena.objects if o not in objs and not o.hide_render]
    for o in ocultos:
        o.hide_render = True
    if not manter_cores:
        for i, o in enumerate(objs):
            o.color = CORES[i % len(CORES)]

    minimo, maximo = _limites(objs)
    centro = (minimo + maximo) / 2
    dims = maximo - minimo
    tamanho = max(dims.length, 1.0)

    camera_dados = bpy.data.cameras.new("preview_cam")
    camera_dados.type = "ORTHO"
    camera_dados.ortho_scale = tamanho * 1.1
    camera_dados.clip_start = 0.1
    camera_dados.clip_end = tamanho * 20
    camera = bpy.data.objects.new("preview_cam", camera_dados)
    cena.collection.objects.link(camera)
    camera_antiga = cena.camera
    cena.camera = camera
    _configurar_render(cena, resolucao)

    arquivos = []
    try:
        for nome in vistas:
            direcao = VISTAS[nome].normalized()
            camera.location = centro + direcao * tamanho * 5
            if nome == "topo":
                camera.rotation_euler = (0, 0, 0)  # olhando -Z, X para a direita, Y para cima
            else:
                camera.rotation_euler = (-direcao).to_track_quat("-Z", "Y").to_euler()
            cena.render.stamp_note_text = (f"{nome} | quadro {camera_dados.ortho_scale:.0f} mm | "
                                           f"peça {dims.x:.1f} x {dims.y:.1f} x {dims.z:.1f} mm")
            cena.render.filepath = str(pasta / f"{nome}.png")
            bpy.ops.render.render(write_still=True)
            arquivos.append(pasta / f"{nome}.png")
    finally:
        cena.camera = camera_antiga
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_dados)
        for o in ocultos:
            o.hide_render = False

    if len(arquivos) == 4:
        return _folha(arquivos, pasta / "folha.png")
    return arquivos[0]
