---
name: modelagem-blender
description: Escreve e altera o modelo.py paramétrico de um projeto usando bpy/bmesh no Blender 5.x — primitivas, booleanas, revolução de perfil, chanfros, arrays, texto, cascas, e o ciclo gerar → ver previews → ajustar. Use sempre que for criar ou mudar geometria de uma peça, ou quando o usuário pedir ajustes de forma/medida.
---

# Modelagem no Blender via script

Pré-requisito: especificação aprovada (skill `grill-me`). Modele na ordem das etapas da
skill `fluxo-projeto` (2a base → 2b recursos → 2c acabamento), com autorrevisão e
aprovação do usuário em cada uma.

O `projetos/<nome>/modelo.py` é a fonte da verdade. Estrutura (ver `projetos/_modelo/modelo.py`):

1. Parâmetros em mm no topo, em MAIÚSCULAS.
2. `construir()` começa com `cena.nova_cena()` e devolve a lista de peças (objetos malha).
3. Bloco `__main__`: exporta STL por peça, salva .blend, gera relatório e previews.

## Ciclo de trabalho

```bash
tools/blender.sh projetos/<nome>/modelo.py 2>&1 | grep -vE "render +\| Saved|^$" | tail -40
```

Depois leia `projetos/<nome>/saida/preview/folha.png` (Read) e o JSON do relatório.
Confira na imagem se a forma bate com a intenção e com as referências. Para detalhe,
leia a vista individual (`iso.png`, `frente.png`, `lado.png`, `topo.png`).
Erro de Python no Blender: o traceback aparece na saída e o comando sai com código 1.

Faça mudanças pequenas por iteração. Peça grande ou complexa: construa por etapas e
gere previews no meio do caminho.

## Biblioteca `bl` (tools/bl)

| Função | O que faz |
| --- | --- |
| `cena.nova_cena()` | Cena vazia em mm |
| `formas.caixa(l, p, a, chanfro)` | Caixa centrada em XY, base em Z=0 |
| `formas.cilindro(raio, altura, vertices, z0)` / `formas.tubo(...)` | Cilindro / tubo no eixo Z |
| `formas.revolucao([(r, z), ...], passos)` | Sólido de revolução a partir de perfil |
| `formas.texto(txt, altura_letra, espessura, fonte)` | Texto 3D em malha |
| `formas.furo_parafuso(alvo, x, y, altura_peca)` | Furo M3 com rebaixo (diâmetros ajustáveis) |
| `malha.aplicar_transformacoes(obj)` | Aplica rotação e escala |
| `malha.aplicar_modificadores(obj)` | Congela a pilha de modificadores |
| `malha.booleana(alvo, ferramenta, "DIFFERENCE"/"UNION"/"INTERSECT")` | Booleana (solver MANIFOLD), apaga a ferramenta |
| `malha.juntar(objs, nome)` | Junta objetos num só |
| `malha.apoiar_na_mesa(obj)` | Base em Z=0, centrado em XY |
| `malha.limpar(obj)` | Funde vértices duplicados, corrige normais |
| `malha.manter_maior_ilha(obj)` | Apaga todas as partes soltas menos a maior (fragmentos de remesh/decimação) |
| `pintura.exportar_3mf(obj, cores, caminho, suportes=None)` + `pintura.triangular`, `pintura.cores_vazias` | 3MF com pintura de cor por triângulo (`paint_color`) e de suporte (`paint_supports`) no formato do Bambu: multicor sem separar partes |
| `malha.fechar_pincamentos(obj, raio)` | Une esferinhas onde partes se tocam só numa aresta/ponto (vira "manifold = no" no fatiador) |
| `exportar.stl_por_peca(objs, pasta)` | Um STL por objeto |
| `checagem.relatorio(objs, caminho)` | Relatório de imprimibilidade |
| `preview.renderizar(objs, pasta)` | Previews + folha 2x2 |
| `logo.svg_para_malha(svg, largura_mm, altura_mm)` | SVG em relevo (skill `logo-em-relevo`) |
| `logo.enrolar_em_revolucao(obj, raio_de_z, z_centro)` | Enrola relevo plano em superfície de revolução com barriga |
| `preview.renderizar(objs, pasta, manter_cores=True)` | Previews com a cor de cada objeto (`obj.color`) em vez da paleta |
| `formas.prisma(pontos, comprimento, eixo)` | Polígono 2D extrudado e centrado num eixo: furo em gota, cunha a 45°, aba, sulco com pontas a 45° |
| `formas.rosca_externa(raio_raiz, profundidade, passo, z_inicio, voltas)` | Filete helicoidal para UNION num colar; corte o excesso no topo com DIFFERENCE |
| `contorno.Contorno(largura, comprimento, raio)` + `.amostrar(passo)` | Planta em retângulo arredondado ou estádio, amostrada por comprimento de arco |
| `contorno.estrias(amostra, passo, sulco, fundo, forma)` | Deslocamento de estrias retas ou caneluras côncavas (número inteiro na volta) |
| `contorno.Contorno(..., raio_y=...)` | Cantos elípticos: estádio de um original escalado com fatores diferentes por eixo |
| `cotas.vista(objs, "frente"/"lado"/"topo"/"iso", arquivo, titulo, regiao=...)` + `cotas.linha`/`cotas.nota` + `cotas.folha(...)` | Folha de medidas para o cliente validar: explodido, cortes (`cotas.corte`) e detalhes ampliados, cotas desenhadas com Pillow. Exemplos: `projetos/*/cotas.py` |
| `contorno.solido(aneis, nome, ciclo)` | Liga anéis `amostra.anel(z, deslocamento)` num sólido sem booleana: potes, cestos, lixeiras, aros, vãos com ressalto |

Ao criar um utilitário reaproveitável, coloque em `tools/bl/` e documente aqui.

## Receitas

Snippets testáveis em [referencia-bpy.md](referencia-bpy.md): caixa com chanfro, cilindro
oco, revolução de perfil (canecas, vasos, copos), furos e rebaixos, array, texto 3D,
casca (solidify), arredondamento (bevel), deformação em curva.

Escolha a técnica pela forma:

| Forma | Técnica |
| --- | --- |
| Peça prismática, suporte, caixa | Primitivas + booleanas + bevel |
| Peça de revolução (caneca, vaso, puxador) | Perfil 2D + `spin` (bmesh) |
| Casca fina (vaso, capa) | Sólido + `SOLIDIFY` ou booleana com cópia reduzida |
| Pote/cesto/lixeira de planta arredondada, com estrias ou caneluras | `contorno.solido` com anéis (parede, folga e estria são deslocamentos na normal; ponta do sulco a 45° = anel liso em z e anel estriado em z ± fundo). Sem booleana, malha limpa. Deslocamento para dentro maior que o raio do canto inverte o canto: use raio > recuo |
| Padrão repetido (grade, furos) | `ARRAY` ou laço criando ferramentas e uma booleana UNION antes da DIFFERENCE |
| Texto | `text_add` + `extrude` + converter para malha |
| Logo/desenho | Skill `logo-em-relevo` |
| Textura de superfície (martelado, ranhuras) | Subdivisão + `DISPLACE` com textura procedural, aplicada |
| Martelado em peça de revolução | Revolução densa + deslocar só os vértices do perfil externo na normal, com covinhas sorteadas (Poisson) e máscara para áreas lisas (numpy, ver `martelar` em projetos/caneca-jo-spinola) |
| Forma orgânica contínua (espuma, nuvem, gota) | Metaballs num só objeto → `bpy.data.meshes.new_from_object` → UNION. Raio visível ≈ 0,568 × `radius` (threshold 0,6, stiffness 2). Massas isoladas viram "bolinhas"; massas grandes sobrepostas viram relevo contínuo. Corte o que invade outra peça com um sólido de folga e confira ilhas soltas no relatório |
| Colorir malha orgânica (rosto, cabelo, barba) em até 4 cores | Pintura por triângulo (`bl.pintura`), sem booleana. Regiões: linha do cabelo/barba como pontos nas vistas com grade → raycast → ângulo em volta do eixo da cabeça → z limite por ângulo; polígonos vistos de frente + teste de visibilidade (raycast) para olhos, boca, sobrancelhas; íris/pupila = círculo em volta da normal média da esclera; subdividir só os triângulos dos olhos; limpar manchas pequenas por componentes conexos (ver `pintar` em projetos/cabeca-homem-realista). Barba rala/por fazer: risquinhos verticais ~1,4 x 0,55 mm espalhados por Poisson (`pontilhar`), não mancha cheia nem bolinhas (cliente rejeitou as duas); confira no G-code a parede externa |
| Separar regiões de malha IA para pintar (chifres, olhos, mechas) | Curvatura média por vértice suavizada (> 0 = côncavo); faces acima do limiar são "vinco"; componentes conexas sem atravessar vinco = regiões; escolha a região pelo centro. Faces de vinco herdam a região vizinha só por poucos anéis (vinco comprido leva a cor longe). Para divisas por regra (polígono, linha do cabelo): refaça uma faixa de ~1,2 mm em volta crescendo as cores dos dois lados até o vinco e alise com borrão nos vértices (ver `regioes_por_vinco`, `ajustar_borda` em projetos/Asta) |
| Subdividir só uma região de malha triangulada | Não use `bmesh.ops.subdivide_edges` repetido: deixou arestas com 4 faces (mesmo triangulando entre as rodadas). Use corte no meio em numpy: triângulo com 3 arestas marcadas vira 4, com 1 vira 2, com 2 marca a 3ª (`_subdividir` em projetos/Asta) |
| Separar cabeça de malha IA de corpo inteiro (gola encosta no queixo) | Apagar faces abaixo de uma superfície de corte (plano + lombada nos lados + piso sob o queixo) e descer a borda na vertical até uma base plana: cabeça fica na pose original (ver `cortar_pescoco` em projetos/cabeca-homem-realista) |
| Malha de terceiro/IA que as booleanas recusam (não-manifold) | Modificador REMESH `VOXEL` (0,1 mm numa peça de 80 mm: 4 s, 6 milhões de tri) → DECIMATE `COLLAPSE` até ~1,5 milhão → `malha.manter_maior_ilha`. Sai fechada e sem cruzamentos; depois disso MANIFOLD corta em segundos (ver projetos/IRON-MAIDEN) |
| Engrossar lâmina fina (bandeira, lâmina) em malha de terceiro | Espessura por raycast na normal, cada lado anda metade do que falta. SÓ dentro de caixas em volta da lâmina: dentes, rugas e brasões também medem fino e incham. Uma ou duas rodadas com teto de deslocamento; normais e deslocamento suavizados nos vizinhos. Remesh voxel depois funde os cruzamentos (`engrossar` em projetos/IRON-MAIDEN) |
| Patas, dentes ou outra parte ruim de malha IA (dedos de "mão", 5ª pata, cones fundidos na língua) | Apagar a parte (caixa + plano + componente conexa), tapar e modelar a peça nova com primitivas (elipsoides, tubos, cones) unidas no remesh voxel; pintar pela geometria conhecida das primitivas, não por detecção de relevo (falhou em dentes da IA). Dentes: elipsoides achatados meio enterrados (topo arredondado), na gengiva FORA da língua; dentro da boca = oclusão por raios; ver projetos/Cachorrinha |
| Tubo/alça copiado de desenho | Trace a linha de centro da imagem (raios a partir de um ponto interno, meio da faixa de pixels), escale pelas pontas, suavize e varra uma seção. Ligue trechos retos ao traçado com Bézier (suavização Laplaciana deixa dobra na ponta fixa) |

## Regras

- Malha final fechada (manifold). Depois de booleanas, rode `malha.limpar(obj)` e confira
  `malha_fechada` no relatório.
- Booleanas: ferramenta deve atravessar a superfície (estenda 0.5–1 mm além) para evitar
  faces coplanares.
- Contagem de triângulos: mantenha abaixo de ~500 mil por peça. `bevel.segments` e
  `vertices` de cilindros são os vilões. Cilindro: 64–128 vértices bastam.
- Textura por `DISPLACE` exige subdivisão densa: aplique, depois use `DECIMATE` (ratio
  0.3–0.5) se o arquivo ficar pesado.
- Dimensão funcional (encaixe, furo de parafuso) vem de parâmetro com folga explícita
  (`config/impressora.json` → `projeto`).
- Registre no README do projeto qualquer decisão não óbvia (orientação, folgas, divisões).
- Peça "em nova escala" a partir de um original: o desenho continua IGUAL ao original (layout,
  divisões, alças, proporções), só com escala por eixo; espessuras, estrias, folgas e furos
  ficam com as medidas do original. Meça o original por cortes (`saida/original/`) e escreva
  as posições como `medida_original * K_eixo`. Não "melhore" o layout sem o usuário pedir.
