"""Preparação de cena: unidades em mm e cena vazia."""
import bpy


def configurar_mm(cena=None):
    """1 unidade = 1 mm. O STL exportado sai em mm, como o Bambu Studio espera."""
    cena = cena or bpy.context.scene
    cena.unit_settings.system = "METRIC"
    cena.unit_settings.scale_length = 0.001
    cena.unit_settings.length_unit = "MILLIMETERS"
    for area in getattr(bpy.context.screen, "areas", []):
        if area.type == "VIEW_3D":
            area.spaces.active.clip_end = 10000
    return cena


def nova_cena():
    """Apaga tudo e devolve uma cena vazia em mm."""
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    else:
        # No Blender aberto (ponte ao vivo) não recarrega a sessão do usuário.
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for colecao in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
            for item in list(colecao):
                if item.users == 0:
                    colecao.remove(item)
    return configurar_mm()


def colecao(nome):
    """Devolve (criando se preciso) uma coleção ligada à cena."""
    col = bpy.data.collections.get(nome) or bpy.data.collections.new(nome)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col
