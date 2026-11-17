# Receitas bpy (testadas no Blender 5.2)

Todas em mm, dentro de `construir()` depois de `cena.nova_cena()`.
Importe: `import bpy, bmesh, math` e `from bl import cena, formas, malha, logo`.

## Formas base (`tools/bl/formas.py`)

```python
c = formas.caixa(40, 30, 10, chanfro=1.0, nome="base")        # centrada em XY, base em Z=0
cil = formas.cilindro(raio=10, altura=20, vertices=96, z0=0)  # eixo Z
t = formas.tubo(raio_externo=12, raio_interno=10, altura=25)
tx = formas.texto("Olá", altura_letra=8, espessura=1.2, fonte="/usr/share/fonts/...ttf")
formas.furo_parafuso(c, x=10, y=0, altura_peca=10)            # M3 passante com rebaixo
```

## Revolução de perfil (canecas, copos, vasos, puxadores)

Perfil = lista `(raio, z)` do eixo para fora e de volta ao eixo. Cada ponto vira um anel.

```python
R, H, E, F = 42, 95, 2.4, 3     # raio externo, altura, parede, fundo
caneca = formas.revolucao([
    (0, 0), (R - 3, 0), (R, 3),  # fundo com chanfro de 3 mm (sem pé de elefante)
    (R, H), (R - E, H),          # borda
    (R - E, F), (0, F),          # parede interna e fundo interno
], passos=128, nome="caneca")
```

Formas curvas (barriga de caneca Moscow Mule): gere o perfil com uma função,
por exemplo `[(R + 4 * math.sin(math.pi * z / H), z) for z in range(0, H + 1, 2)]`
para o lado externo e o mesmo deslocado de `-E` para o interno.

## Booleanas

```python
malha.booleana(alvo, ferramenta, "DIFFERENCE")   # também "UNION" e "INTERSECT"
```

- Padrão: solver `MANIFOLD` (rápido, saída fechada). Exige entradas fechadas.
- Ferramenta deve passar 0.5–1 mm além da face que corta.
- Muitas ferramentas: junte primeiro (`malha.juntar`) ou use ARRAY, depois uma booleana só.

## Grade de furos (ARRAY na ferramenta)

```python
placa = formas.caixa(60, 40, 3, nome="placa")
furo = formas.cilindro(2, 5, 32, z0=-1, nome="furo")
furo.location.x, furo.location.y = -20, -10
for nome, n, passo in (("ax", 5, (10, 0, 0)), ("ay", 3, (0, 10, 0))):
    arr = furo.modifiers.new(nome, "ARRAY")
    arr.count = n
    arr.use_relative_offset = False
    arr.use_constant_offset = True
    arr.constant_offset_displace = passo
malha.aplicar_modificadores(furo)
malha.booleana(placa, furo, "DIFFERENCE")
```

## Arredondar arestas

```python
mod = obj.modifiers.new("arredondar", "BEVEL")
mod.width = 2.0
mod.segments = 4                  # 3–6 basta para impressão
mod.limit_method = "ANGLE"
mod.angle_limit = math.radians(60)
malha.aplicar_modificadores(obj)
```

Arestas da base (contato com a mesa): prefira chanfro (`segments = 1`) a arredondado.

## Casca (SOLIDIFY)

Para dar espessura a uma superfície aberta (vaso, capa):

```python
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > H - 0.1], context="FACES")
bm.to_mesh(obj.data); bm.free()
mod = obj.modifiers.new("casca", "SOLIDIFY")
mod.thickness = 1.6
mod.offset = -1                  # cresce para dentro, mantém a medida externa
malha.aplicar_modificadores(obj)
```

## Textura martelada (DISPLACE + VORONOI) só na parede externa

A malha precisa de vértices densos onde a textura vai: perfil com ponto a cada 1 mm e
`passos=256` na revolução.

```python
R, H = 30, 50
perfil = [(0, 0), (R, 0)] + [(R, z) for z in range(1, H)] + [(R, H), (R - 2.4, H), (R - 2.4, 3), (0, 3)]
copo = formas.revolucao(perfil, passos=256, nome="copo")
grupo = copo.vertex_groups.new(name="externa")
grupo.add([v.index for v in copo.data.vertices
           if math.hypot(v.co.x, v.co.y) > R - 0.01 and 2 < v.co.z < H - 2], 1.0, "REPLACE")
tex = bpy.data.textures.new("martelo", "VORONOI")
tex.noise_scale = 6.0            # tamanho das marcas (mm, aprox.). Ajuste olhando o preview
mod = copo.modifiers.new("martelado", "DISPLACE")
mod.texture = tex
mod.texture_coords = "GLOBAL"
mod.direction = "NORMAL"
mod.vertex_group = "externa"
mod.strength = -0.6              # negativo = afunda; mantenha |strength| < parede - 1.2 mm
mod.mid_level = 0.0
malha.aplicar_modificadores(copo)
```

## Logo/texto enrolado em cilindro

```python
lg = logo.svg_para_malha("referencias/logo.svg", largura_mm=50, altura_mm=1.0)
logo.enrolar_em_cilindro(lg, raio=R, z_centro=H / 2, afundar=0.4)
malha.booleana(caneca, lg, "UNION")
```

Detalhes na skill `logo-em-relevo`.

## Dividir peça grande

```python
metade = obj.copy(); metade.data = obj.data.copy(); bpy.context.scene.collection.objects.link(metade)
corte = formas.caixa(400, 400, 400, nome="corte"); corte.location = (200, 0, -100)  # corta em X=0, sem face coplanar na base
malha.booleana(obj, corte, "DIFFERENCE", apagar_ferramenta=False)
malha.booleana(metade, corte, "INTERSECT")
```

Adicione pinos e furos de alinhamento (folga 0.2 mm) nas faces de corte.

## Malha direta com bmesh (formas sem primitiva)

Polígono 2D qualquer (lista de pontos XY) extrudado em Z:

```python
pontos = [(0, 0), (30, 0), (30, 5), (5, 5), (5, 20), (0, 20)]   # perfil em L
bm = bmesh.new()
face = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pontos])
ret = bmesh.ops.extrude_face_region(bm, geom=[face])
novos = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=novos, vec=(0, 0, 12))             # espessura 12 mm
dados = bpy.data.meshes.new("perfil_l"); bm.to_mesh(dados); bm.free()
obj = bpy.data.objects.new("perfil_l", dados); bpy.context.scene.collection.objects.link(obj)
malha.limpar(obj)                                                 # corrige normais
```
