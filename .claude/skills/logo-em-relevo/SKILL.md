---
name: logo-em-relevo
description: Transforma imagem, logo, assinatura ou texto em geometria 3D — relevo (alto-relevo) ou gravação (baixo-relevo), em superfície plana ou enrolado em cilindro (caneca, copo, porta-lápis). Inclui vetorização (imagem -> SVG), escala, regras de detalhe mínimo e multicor. Use quando o usuário trouxer um logo/arte para aplicar numa peça, ou pedir placa, chaveiro, carimbo, plaquinha com nome.
---

# Logo em relevo

## 1. Preparar a imagem

Melhor entrada: SVG original do logo (peça ao usuário se existir). Senão, PNG/JPEG
com alto contraste, fundo liso.

Fotos de produto (logo numa caneca, por exemplo) não servem para vetorizar direto:
perspectiva, reflexos e textura viram ruído. Use o arquivo do logo ou peça um.

## 2. Vetorizar

```bash
python3 tools/imagem_para_svg.py projetos/<nome>/referencias/logo.png \
  -o projetos/<nome>/saida/logo.svg --previa projetos/<nome>/saida/logo_previa.png
```

Leia `logo_previa.png` (Read): preto = vira geometria. Ajuste e repita:

| Problema | Ajuste |
| --- | --- |
| Partes faltando / traços finos sumindo | `--limiar 160` (mais alto pega mais cinza) |
| Fundo/sujeira virando geometria | `--limiar 90` |
| Logo claro em fundo escuro | `--inverter` |
| Contorno serrilhado | `--desfoque 1.5` e/ou `--suavizar 3` |
| Cantos vivos arredondados demais (texto) | `--suavizar 0 --tolerancia 0.6` |
| Manchinhas soltas | `--area-min 200` |

Com `potrace` instalado (`sudo apt install potrace`, pedir ao usuário) o script usa
potrace automaticamente, com curvas melhores. Sem ele, usa o traçador interno.

Uma moldura circular ou retangular do logo pode virar um anel solto. Decida com o
usuário se ela fica, sai ou vira a borda da peça.

## 3. Virar malha

```python
from bl import logo, malha, formas
lg = logo.svg_para_malha(SAIDA / "logo.svg", largura_mm=LARGURA_LOGO, altura_mm=ALTURA_RELEVO)
```

Sai centrado em XY, base em Z=0, desenho no plano XY, relevo em +Z.

## 4. Aplicar na peça

**Plano, alto-relevo** (placa, chaveiro):
```python
base = formas.caixa(70, 70, 3, chanfro=0.6, nome="placa")
lg.location.z = 3 - 0.2          # afunda 0.2 mm para a UNION não ter face coincidente
malha.booleana(base, lg, "UNION")
```

**Plano, gravação** (baixo-relevo): posicione o logo atravessando o topo
(`lg.location.z = topo - profundidade`, altura do logo = profundidade + 1) e use
`"DIFFERENCE"`.

**Cilindro** (caneca, copo):
```python
logo.enrolar_em_cilindro(lg, raio=R_EXTERNO, z_centro=ALTURA / 2, afundar=0.4)
malha.booleana(corpo, lg, "UNION")
```
Para gravar no cilindro: `altura_mm` do logo = profundidade + 0.5, `afundar` =
profundidade e `"DIFFERENCE"`. Profundidade máxima = parede − 1.2 mm.
O logo deve caber na parte reta da parede; a função não acompanha barriga/curvatura
vertical.

**Superfície com barriga** (Moscow Mule, vaso, caneca bojuda): use
`logo.enrolar_em_revolucao(lg, raio_de_z, z_centro, afundar=0.4, passo_mm=1.5)`, onde
`raio_de_z(z)` é a mesma função do perfil externo usada na revolução. Ela fatia o logo em X
e Y e acompanha o raio em cada altura. Testado na caneca-jo-spinola (Ø64 numa barriga de
Ø106–112): malha fechada, sem autointerseções após `malha.booleana(..., "UNION")`.

**Traços finos em logo de baixa resolução** (ex.: JPEG de 500 px): antes de vetorizar,
amplie 4x com Pillow (LANCZOS), desfoque com raio de ~2 px, binarize e engrosse o preto com
`ImageFilter.MinFilter(n)`. Cada 4 px de n na imagem ampliada somam ~1 px original ao traço.
Salve o resultado em `saida/`, nunca em `referencias/`.

## 5. Regras de tamanho (bico 0.4 mm)

- Traço mais fino do logo na escala final ≥ 0.8 mm (ideal 1.0 mm). Calcule:
  espessura_traço_px × largura_mm / largura_imagem_px. Se ficar abaixo, aumente o logo,
  simplifique a arte ou engrosse com `--limiar` mais alto.
- Texto: letras ≥ 4 mm de altura (≥ 6 mm para fonte cursiva).
- Altura do relevo: 0.6–1.2 mm. Gravação: 0.6–1.0 mm.
- Relevo em parede vertical (caneca de pé): ok sem suporte até ~1.2 mm de saliência.
- Para detalhe fino, fatie com `0.12mm Fine @BBL A1M` ou `0.16mm Optimal @BBL A1M`.

## 6. Duas cores

- Placa plana sem AMS: relevo começa numa altura múltipla de 0.2 mm; o usuário pausa e
  troca o filamento nessa camada. Informe a altura exata.
- Com AMS lite: exporte o logo como peça separada (`exportar.stl_por_peca([base, lg], ...)`,
  sem UNION; o logo pode afundar 0.2 mm na base) e gere o projeto com
  `python3 tools/fatiar.py base.stl logo.stl --multicor --filamento ... --filamento ...`.
  O fatiamento final é no Bambu Studio (skill `preparar-impressao`, seção Multicor).
