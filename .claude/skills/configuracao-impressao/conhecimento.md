# Conhecimento de impressão FDM (A1 mini, bico 0.4, PLA/PETG)

Compilado de manuais e testes publicados. Marcação da origem:
**[M]** medido em teste; **[O]** documentação oficial (Bambu Lab, Prusa, OrcaSlicer, Hubs);
**[C]** relato da comunidade; **[T]** testado nesta máquina; **[I]** inferência, não verificada.

Quando um valor daqui virar regra do repositório, ele vai para `config/impressora.json`
ou para a skill correspondente. Quando a prática contradisser algo daqui, corrija este
arquivo e registre a data.

## 1. Resistência

- **Paredes valem mais que preenchimento.** Com o mesmo peso de peça, 5 paredes e 10% de
  preenchimento deram ~22% mais resistência que 2 paredes e 42%. [M] CNC Kitchen via
  [3ders](https://www.3ders.org/articles/20190208-stefan-at-cnc-kitchen-experimenting-with-smart-infill-for-stronger-3d-prints.html)
- Gancho em pé, 20% de preenchimento: 2 paredes ~20 kg; 4 paredes ~33 kg; 3 paredes com
  linha 133% ~37 kg. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/the-effect-of-extrusion-width-on-strength-and-quality-of-3d-prints)
- Preenchimento: 10–20% é o ponto ideal; acima de 40% raramente compensa; subir paredes
  dá o mesmo ganho que subir preenchimento acima de 20%. [O] [Prusa](https://blog.prusa3d.com/everything-you-need-to-know-about-infills_43579/)
- **Direção das camadas é o ponto fraco.** Tração em PLA, camada 0.2: deitado 63 MPa,
  45° 40 MPa, em pé 31 MPa (metade). [M] [CNC Kitchen](https://www.cnckitchen.com/blog/stop-printing-flat-the-45-secret-for-stronger-parts)
  Oriente para a carga ficar no plano XY. [O] [Bambu](https://wiki.bambulab.com/en/filament/pla)
- **Altura de camada x resistência** (bico 0.4): 0.05–0.2 mm iguais deitados; 0.3 pior;
  0.4 muito pior. Em pé, 0.15 foi o mais forte. Regra: camada ≤ metade do bico (≤ 0.2);
  abaixo de 0.15 só aumenta tempo. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/the-influence-of-layer-height-on-the-strength-of-fdm-3d-prints)
- **Temperatura x adesão entre camadas** (corpo de prova em pé): PLA 190 °C 20 MPa,
  210 °C 39, 230 °C 40 (pico), 270 °C 32. PETG pico em 245 °C. Para resistência, use o
  topo da faixa do filamento; para aparência, a parte de baixo. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/the-influence-of-extrusion-temperature-on-layer-adhesion)
- Mais ventilação diminui a adesão entre camadas (estudo cita ~40% a menos com ventoinha
  ligada). [C/I] [ABCM](https://abcm.org.br/proceedings/view/COB2021/0310)
- Padrões de preenchimento: só há classificação qualitativa. Fortes em XY e Z: gyroid,
  cubic, grid, honeycomb. Fracos em Z: rectilinear/zig-zag. Não estruturais: lightning,
  support cubic. [O] [OrcaSlicer](https://www.orcaslicer.com/wiki/print_settings/strength/strength_settings_patterns)
- Bambu: tri-hexagon "um dos mais fortes à tração"; honeycomb rígido e resistente a impacto
  com ~25% mais material. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/fill-patterns)

Resumo prático: peça funcional = 3–4 paredes + 15–25% gyroid/cubic + camada 0.20 +
orientação com carga em XY. Carga alta = preset Strength (6 paredes, 25%).

## 2. Costura (seam)

- **Teste nesta A1 mini** (cilindro Ø30, 2026-10-17): `back` → costura em +Y (fundo) em
  todas as camadas; `aligned` → -Y (frente); `nearest` e `random` → espalhada (desvio
  ~110°). [T]
- `nearest` escolhe canto côncavo, depois convexo, depois qualquer ponto sem overhang; sem
  canto na camada, pega o ponto mais perto do fim do caminho anterior. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/Seam)
  Em peça redonda isso espalha a costura. [T]
- `random` é a causa mais comum de "pontinhos" (zits) na parede; solução: `aligned`,
  `back` ou pintura de costura. [O] [Bambu](https://wiki.bambulab.com/en/knowledge-sharing/dots-on-the-print)
- Cilindro não consegue esconder costura. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/Seam)
  Costura nunca é eliminada; é mais visível em cilindro. [O] [Prusa](https://help.prusa3d.com/article/seam-position_151069)
- **Scarf seam** (costura de cachecol, `seam_slope_type`): rampa de fluxo no início/fim
  da volta; dilui a marca em curva suave; cantos mais vivos que 155° continuam com costura
  comum; nunca na primeira camada nem em vaso espiral. [O] [OrcaSlicer](https://www.orcaslicer.com/wiki/print_settings/quality/quality_settings_seam)
  - Reduz, não elimina. [C] [fórum Bambu](https://forum.bambulab.com/t/scarf-joints-doesnt-seam-to-always-work/157900)
  - PLA Matte lascou na costura; parede externa a ~40 mm/s resolveu. [C] [fórum Bambu](https://forum.bambulab.com/t/scarf-seams-will-cause-small-chips-on-outer-walls/155926)
  - Bambu Studio tem menos opções de scarf que o OrcaSlicer. [C] [fórum Bambu](https://forum.bambulab.com/t/limited-settings-for-scarf-seam-in-bambu-studio-cpmpared-to-orca-slicer/233445)
- Outras dicas oficiais para costura: 3 paredes, menos objetos por placa, um pouco mais
  quente e parede externa mais lenta, ou vaso espiral. [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/seam)
- Sem retração antes do wipe a costura da parede externa fica melhor (padrão 0%). [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/parameter/retraction)
- Vaso espiral elimina a costura, mas só 1 parede e sem preenchimento. [O] [Prusa](https://help.prusa3d.com/article/seam-position_151069)
- Caneca com alça: costura atrás, junto da alça (alça em +Y + `back`). [I]

## 3. Preenchimento

- Padrão por uso [O] [Prusa](https://blog.prusa3d.com/everything-you-need-to-know-about-infills_43579/):
  velocidade → rectilinear/line; economia → adaptive cubic (~25% menos material);
  resistência em todas as direções → gyroid; flexível → concentric/archimedean chords.
- Grid: cruzamentos acumulam material, bico raspa em alta velocidade. Grid/triangles com
  bico batendo: troque por line, rectilinear, gyroid ou concentric. Peça plana grande que
  empena: gyroid ≤ 25%. [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/warping-falling-off-collapsing)
- Gyroid espalha a contração (menos empeno), mas fatia devagar. [O] [OrcaSlicer](https://www.orcaslicer.com/wiki/print_settings/strength/strength_settings_patterns)
- Lightning só sustenta topo, sem resistência relevante. [O] [Ultimaker](https://ultimaker.com/learn/how-to-print-like-a-flash-with-lightning-infill/)
- Peça alta na A1: evitar grid (cruzamentos causam vibração), usar aligned rectilinear ou
  gyroid. [C] [UNBC](https://sparklab.unbc.ca/?p=672)
- TPU: grid (padrões complexos saem mal em flexível); menos paredes e cascas para flexionar. [O] [Prusa](https://help.prusa3d.com/article/flexible-materials_2057)

## 4. Paredes, espessuras e detalhes mínimos

- Largura de linha 0.42–0.45 mm: 1/2/3/4 paredes ≈ 0.45/0.9/1.35/1.8 mm; mais fino que
  uma linha não imprime. [O] [Prusa](https://help.prusa3d.com/en/article/modeling-with-3d-printing-in-mind_164135/)
- Linhas se sobrepõem: 2 linhas de 0.4 com camada 0.2 dão ≈ 0.76 mm, não 0.8. [O] [Ellis](https://ellis3dp.com/Print-Tuning-Guide/articles/misconceptions.html)
  Por isso `config/impressora.json` usa parede mínima 1.2 mm (≈ 3 linhas) e detalhe
  mínimo 0.8 mm (≈ 2 linhas).
- Gerador `classic` descarta o que for mais fino que a largura de linha; `arachne` varia a
  largura e imprime texto/detalhe pequeno. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/wall-generator)
- Texto: relevo/gravação com traço ≥ 0.6 mm e altura ~2 mm no mínimo [O] [Formlabs](https://formlabs.com/blog/fdm-vs-sla-vs-sls-how-to-choose-the-right-3d-printing-technology/);
  letra de ~10 mm é confiável, 4 mm é o limite prático; profundidade em múltiplos da
  camada (0.6–0.8 mm). [C] [fórum Prusa](https://forum.prusa3d.com/forum/english-forum-original-prusa-i3-mk4s-how-do-i-print-this/issue-with-debossed-text/)
- Pinos < 5 mm saem fracos: filete na base. Cantos internos sempre ficam com raio do bico. [O] [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)

## 5. Tolerâncias e encaixes

- Furos saem menores: contração, excesso de material na parte interna da curva, facetas do
  STL. CNC Kitchen mediu furos ~0.25 mm menores que no CAD. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong)
  Se o furo sai 0.1 mm pequeno, compensação XY de +0.05 (metade, por lado). [O] [Slic3r](https://manual.slic3r.org/troubleshooting/dimension-errors)
- Prusa: precisão ~0.2 mm; peças móveis a partir de 0.3 mm de folga. [O] [Prusa](https://help.prusa3d.com/en/article/modeling-with-3d-printing-in-mind_164135/)
  Hubs: ±0.5% (mínimo ±0.5 mm); snap-fit com 0.5 mm. [O] [Hubs](https://www.hubs.com/knowledge-base/dimensional-accuracy-3d-printed-parts/)
- Fontes misturam folga "por lado" e "no diâmetro". **Sempre imprima peça de teste** para
  encaixe crítico. Modelo de teste de referência: furos sextavados com 0/0.05/0.1/0.2/0.3/0.4
  de folga. [O] [OrcaSlicer](https://www.orcaslicer.com/wiki/calibration/tolerance_calib)
- Furo horizontal cede no topo: formato gota ou topo chanfrado; furo vertical crítico:
  imprimir menor e furar. [O] [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
  Um teste achou encaixe de pino só com gota ≥ 30°. [C] [MakerWorld](https://makerworld.com/models/2085522)
- **Inserto M3 de latão (por calor)**: furo de 4.2 mm no modelo foi o ponto ideal (o
  datasheet diz 4.0); parede mínima 1.6 mm; furo cego 1 mm mais fundo que o inserto;
  ferro 10–20 °C acima da temperatura de impressão. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong),
  [O] [dicas](https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts)
- M3 em PETG, torque/arrancamento: parafuso direto no plástico 1 Nm/118 kg; inserto 3 Nm/119 kg;
  porca embutida por baixo ~2 Nm/166 kg. Junta que abre muitas vezes: inserto. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment)
- Snap-fit: nunca com a haste no eixo Z; folga 0.5 mm; filete na raiz ≥ 0.5× a espessura;
  largura ≥ 5 mm; PLA é quebradiço, prefira PETG. [O] [Hubs](https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/)
- Pé de elefante: calibrar (cubo 25x25x10, compensação 0, sem brim; valor = média do
  excesso X/Y) [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot);
  ou chanfrar a aresta da base. [O] [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)

## 6. Overhang, ponte e suporte

- Overhang até 45° sem suporte [O] [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/);
  Prusa: 45–60° imprime limpo. Bambu: abaixo de 45° (medido da mesa) suporte; PLA ~205 °C
  e ventoinha de overhang 100% ajudam. [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/overhang)
- Ponte < 5 mm sem marcas [O] [Hubs](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/);
  até 10 mm aceitável. Ponte caindo: `bridge_flow` 1.4–1.7 em PLA, velocidade 10–50. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/parameter/bridge)
- Filete virado para a mesa vira overhang íngreme: use chanfro. [O] [Prusa](https://help.prusa3d.com/en/article/modeling-with-3d-printing-in-mind_164135/)
- Suporte normal para overhang plano grande; árvore para pequeno/complexo/orgânico. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/support)
- Bambu Studio não tem "make overhang printable" (é do OrcaSlicer). [O] código-fonte.

## 7. Mesa móvel (A1 mini é "bed slinger")

- A mesa é o eixo Y. [O] [Bambu](https://wiki.bambulab.com/en/a1-mini/manual/intro-a1-mini)
- Peça alta e fina é derrubada pelo movimento: brim ou suporte; ou reduzir velocidade e
  aceleração 20–30%; ou deitar a peça. [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/warping-falling-off-collapsing)
- Comunidade: girar para a maior dimensão (incluindo suporte) ficar em Y; suporte "tree
  strong" ou ponto de suporte pintado no meio da altura para travar. [C] [fórum Bambu](https://forum.bambulab.com/t/bed-slinger-problem/182399)
  Outro guia sugere alinhar em X: fontes conflitam. [C/I] [UNBC](https://sparklab.unbc.ca/?p=672)
- Guia de universidade para A1: deslocamento < 400 mm/s, aceleração < 3000 mm/s², camada
  mínima ~10 s, brim 5–10 mm. [C] [UNBC](https://sparklab.unbc.ca/?p=672)
- Regra prática do repositório: altura > 3× a menor largura da base → brim
  `outer_only` 5–8 mm e avisar o usuário. [I]

## 8. Malha antes de fatiar

- Blender 3D-Print Toolbox verifica: não-manifold, normais invertidas, interseções, faces
  degeneradas, faces não-planas ("distorted" → triangular), espessura e overhang. [O]
  [Blender](https://docs.blender.org/manual/en/3.3/addons/mesh/3d_print_toolbox.html)
  Nosso `tools/bl/checagem.py` cobre todos esses itens.
- **Triangule antes de deformar**: faces não-planas viram triângulos dobrados no STL. [O]
  (mesma fonte) e [T] (logo enrolado na caneca gerou milhares de cruzamentos até
  triangular antes de curvar).
- Como defeito aparece no fatiador:
  - 2401 arestas não-manifold fizeram o Bambu Studio preencher um telhado inclinado como
    plano. [C] [fórum Bambu](https://forum.bambulab.com/t/wrong-geometry-after-slicing-why/131926)
  - O reparo do Bambu fecha a malha onde está quebrada e pode encher uma cavidade
    intencional. [C] [fórum Bambu](https://forum.bambulab.com/t/bambu-studio-filling-cavity/198864)
  - Buracos, sobreposições e regiões finas causaram camadas faltando aleatórias. [C] [fórum Prusa](https://forum.prusa3d.com/forum/prusaslicer/sliced-stl-has-random-missing-horizontal-layers/)
  - Mensagens do Bambu: "Error: %d non-manifold edges", "Info: %d open edges",
    "Object can't be printed for empty layer between X and Y" (parte fina demais ou malha
    com defeito). [O] catálogo de strings do Bambu Studio.
- O reparo do Bambu Studio usa ferramenta do Windows: **não existe no Linux**. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/fix-model)
- Fechamento de fendas do fatiador (`slice_closing_radius` 0.049 mm) só fecha frestas
  < ~0.1 mm. [O] código-fonte.
- `malha_fechada` não garante nada sozinho: malha fechada pode ter triângulos se cruzando. [T]
- Booleanas no Blender: nenhum solver acertou todos os casos; `malha.booleana` tenta
  MANIFOLD, FLOAT e EXACT e valida. [T]

## 9. Defeitos: sintoma → causa → ajuste

| Sintoma | Causa provável | Ajuste (em ordem) | Fonte |
| --- | --- | --- | --- |
| Fios entre partes (stringing) | Umidade, temperatura alta, retração | Secar filamento; −5 a −10 °C; retração ≤ 2 mm; `reduce_crossing_wall=1`; bico gasto | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/stringing-oozing), [Prusa](https://help.prusa3d.com/article/stringing-and-oozing_1805) |
| Cantos levantando (warping) | Placa suja, mesa fria, corrente de ar, peça grande | Lavar placa com detergente; mesa +5–10 °C; brim 8–10 mm; gyroid ≤ 25%; tipo de placa certo | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/warping-falling-off-collapsing) |
| Primeira camada não gruda | Gordura dos dedos, placa errada no fatiador | Lavar placa; `--placa` correto; primeira camada 0.25 mm e linha 0.5 | [O] [Bambu](https://wiki.bambulab.com/en/general/textured-PEI-plate-not-working-as-expected) |
| Primeira camada com vãos entre linhas | Bico alto | Nivelamento automático ligado; se persistir, suporte Bambu | [O] [Ellis](https://ellis3dp.com/Print-Tuning-Guide/articles/first_layer_squish.html) |
| Camadas deslocadas (layer shift) | Bico batendo em peça empenada/overhang curvado, cabo/tubo preso, velocidade | Resolver empeno/overhang; checar cabos; "Auto-recovery from step loss" | [O] [Bambu](https://wiki.bambulab.com/en/knowledge-sharing/layer-shifts) |
| Pontinhos/bolhas na parede (zits) | Costura `random`, umidade | `seam_position=aligned` ou `back`; secar filamento; `seam_gap` | [O] [Bambu](https://wiki.bambulab.com/en/knowledge-sharing/dots-on-the-print) |
| Costura aparente em peça redonda | Inevitável em cilindro | `back` + `seam_slope_type=external`; parede externa mais lenta; pintura de costura | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/seam) |
| Topo com furinhos/almofadado (pillowing) | Poucas camadas de topo, preenchimento baixo | `top_shell_layers` +2; densidade +5%; mais ventilação | [C] [Ultimaker](https://ultimaker.com/learn/3d-printing-infill-density-optimizing-strength-and-speed/) |
| Subextrusão (paredes ralas) | Entupimento, velocidade acima da fusão, fluxo | Checar bico; +10 °C em modo rápido; calibrar fluxo; só nos cantos = flow dynamics | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/under-extrusion) |
| Faixas horizontais irregulares | Clipe do hotend solto, altura variável sem suavizar, diâmetro do filamento | Checar clipe; suavizar altura variável; outro rolo | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/severe-layer-artifacts) |
| Ondulação após cantos (ghosting) | Velocidade/aceleração | Reduzir velocidade/aceleração da parede externa | [O] [Prusa](https://help.prusa3d.com/article/ghosting_1801) |
| Overhang caído/enrolado | Ângulo, ventilação, temperatura | Chanfrar a 45°; ventoinha 100%; PLA ~205 °C; suporte | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/overhang) |
| Ponte cedendo | Fluxo/velocidade | `bridge_flow` 1.4–1.7; `bridge_speed` 10–50; vão ≤ 10 mm | [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/parameter/bridge) |
| Peça alta tombando/balançando | Mesa móvel em Y | Brim; reduzir velocidade/aceleração 20–30%; deitar a peça | [O] [Bambu](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/warping-falling-off-collapsing) |
| Camada faltando / região vazia no preview | Malha com defeito ou parte mais fina que a linha | Checagem de malha; `arachne`; engrossar | [C] [fórum Prusa](https://forum.prusa3d.com/forum/prusaslicer/sliced-stl-has-random-missing-horizontal-layers/) |

Altere uma variável por vez entre testes. [O] [Teaching Tech](https://teachingtechyt.github.io/calibration.html)

## 10. Filamentos na A1 mini

- A1 mini imprime PLA, PETG e TPU; não ABS/ASA/PC/PA/PET; bico de aço inox 0.4 (sem
  CF/GF sem bico endurecido); não enclausurar; ambiente 10–30 °C. [O] [Bambu FAQ](https://wiki.bambulab.com/en/a1-mini/manual/faq)
- PEI texturizada: PLA, PETG e TPU sem cola. [O] [Bambu FAQ](https://wiki.bambulab.com/en/a1-mini/manual/faq)
  PETG: cola facilita a remoção. [O] [Bambu](https://wiki.bambulab.com/en/general/how-to-use-bbl-liquid-glue)
- PETG: mais fios, ponte pior, menos detalhe, empena pouco; para tenacidade, mais paredes
  e menos ventilação. [O] [Prusa](https://help.prusa3d.com/en/article/petg_2059)
- TPU: ~20 mm/s no início, máximo 30–40; retração mínima; ventoinha baixa. [O] [Prusa](https://help.prusa3d.com/article/flexible-materials_2057)
  No AMS lite, evitar TPU mais macio que 77D/55D. [O] [Bambu](https://wiki.bambulab.com/en/ams-lite/manual/faq)
- Secagem: PLA 45–50 °C/6–8 h; PETG 55–65 °C/6–8 h; TPU 60 °C/4–6 h. [O] [Prusa](https://help.prusa3d.com/article/drying-filament_332086)
- Recalibrar flow dynamics ao trocar marca de filamento, bico gasto/trocado, filamento
  úmido, mudança de temperatura ou de velocidade volumétrica. K típico 0.02–0.04. [O] [Bambu](https://wiki.bambulab.com/en/software/bambu-studio/calibration_pa)

## 11. Alimento e calor

- FDM não é seguro para alimento: sulcos das camadas guardam bactérias e detergente; bico
  de latão solta metal; pigmentos desconhecidos. Alternativa: revestimento epóxi
  certificado. [O] [Prusa](https://help.prusa3d.com/article/food-safe-fdm-printing_112313)
- PLA amolece a ~55–60 °C (o preset do Bambu usa 45 °C como "vitrificação"); PETG ~80 °C.
  Não lavar PLA na lava-louças. [C] [Snapmaker](https://www.snapmaker.com/blog/petg-glass-transition-temperature/)
- Recozer PLA (100 °C/45 min): +7.5% tração, adesão entre camadas igual, até 10% de
  variação dimensional imprevisível. [M] [CNC Kitchen](https://www.cnckitchen.com/blog/better-performing-3d-prints-with-annealing-but-part-1-pla)
  Ganho de resistência ao calor só com carga leve. [M] [MM Science](https://www.mmscience.eu/journal/issues/march-2021/articles/experimental-analysis-of-temperature-resistance-of-3d-printed-pla-components)
