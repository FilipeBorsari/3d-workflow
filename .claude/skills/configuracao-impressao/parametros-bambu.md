# Parâmetros do Bambu Studio 02.08 (A1 mini, bico 0.4)

Referência para escolher e aplicar configurações com
`python3 tools/fatiar.py peca.stl --ajuste CHAVE=VALOR`.

- **Chave**: nome interno (é o que vai no `--ajuste` e aparece no bloco de configuração do G-code).
- **Interface**: rótulo pt-BR do Bambu Studio (o do usuário está em pt_BR), com o inglês entre parênteses.
- **Padrão**: valor no preset `0.20mm Standard @BBL A1M` + `Bambu PLA Basic @BBL A1M`,
  conferido no G-code fatiado nesta máquina.
- Valores de lista: use exatamente a grafia da coluna Valores. Valor inválido é ignorado em
  silêncio pelo Bambu; o `fatiar.py` detecta e acusa em `erros_cli`.

Fontes: [W] Bambu Lab Wiki (link na linha); [SRC] `PrintConfig.cpp` do BambuStudio;
[P] presets A1M do BambuStudio; [PR] Prusa Knowledge Base.

## Camadas

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `layer_height` | Altura da camada (Layer height) | 0.08–0.28 mm (20–70% do bico) | 0.2 | Prefira trocar o **preset** de processo (0.08/0.12/0.16/0.20/0.24/0.28), que ajusta velocidades, cascas e suporte juntos. [W](https://wiki.bambulab.com/en/software/bambu-studio/layer-height) |
| `initial_layer_print_height` | Altura inicial da camada | mm | 0.2 | Raramente. 0.25 ajuda aderência difícil. [W](https://wiki.bambulab.com/en/general/textured-PEI-plate-not-working-as-expected) |
| `precise_z_height` | (Precise Z height, experimental) | 0/1 | 0 | Altura final exata em peça com encaixe vertical; ajusta as 5 últimas camadas. [W](https://wiki.bambulab.com/en/software/bambu-studio/layer-height) |
| — | Altura variável da camada | só pela interface | — | Peça com curvas suaves no topo (domo, figura). Sempre usar "Smooth" para evitar faixas. Não funciona com suporte Tree Organic. [W](https://wiki.bambulab.com/en/software/bambu-studio/adaptive-layer-height) |

Presets 0.4 da A1M: 0.08 Extra Fine/High Quality, 0.12 Fine/High Quality, 0.16 Optimal/High
Quality, 0.20 Standard, 0.20 Strength (6 paredes, 25% grade), 0.24 Draft, 0.28 Extra Draft.
"High Quality" = mais lento + giroide. [P]

## Costura (seam)

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `seam_position` | Posição da costura (Seam position) | `nearest` (o mais próximo), `aligned` (Alinhado), `back` (Atrás), `random` (Aleatório) | aligned | Ver regras abaixo. [W](https://wiki.bambulab.com/en/software/bambu-studio/Seam) |
| `seam_gap` | Lacuna de costura (Seam gap) | % do bico | 15% | Bolinha na costura: subir um pouco. Furo/vão na costura: baixar. [W](https://wiki.bambulab.com/en/software/bambu-studio/Seam) |
| `seam_slope_type` | Tipo de costura de cachecol (Scarf seam type) | `none`, `external` (Contorno), `all` (Contorno e furo) | none | Costura em rampa: dilui a marca em superfície lisa/curva (caneca, vaso). [SRC] |
| `seam_slope_start_height` | Altura inicial da costura | % da camada | 10% | 100% = costura comum. |
| `seam_slope_min_length` | Comprimento da costura (Scarf length) | mm | 10 | 0 desliga. |
| `scarf_angle_threshold` | (Scarf application angle threshold) | graus | 155 | Scarf só onde o canto é mais aberto que isso (cantos vivos continuam com costura comum). |
| `seam_slope_gap` | (Scarf slope gap) | % | 0 (filamento PLA Basic usa 15%) | — |
| `override_filament_scarf_seam_setting` | Substituir configuração de costura de cachecol de filamento | 0/1 | 0 | Desde 1.10 a scarf também vive no filamento; ligue 1 para o processo mandar. [W](https://wiki.bambulab.com/en/software/bambu-studio/Seam) |
| `seam_placement_away_from_overhangs` | (experimental) | 0/1 | 0 | Costura caindo em overhang. |
| `wipe_speed` | Velocidade de limpeza (Wipe speed) | % do deslocamento | 80% | — |

Regras de costura (Wiki Bambu):
- `nearest` escolhe, em ordem: canto côncavo → canto convexo → qualquer ponto sem overhang.
  Sem canto na camada (cilindro, esfera), pega o ponto mais perto do fim do caminho
  anterior: a costura **se espalha** pela superfície. Evite em peças redondas.
- `aligned` usa os mesmos candidatos, mas prefere o ponto mais próximo do início da camada
  de baixo: costura vira uma linha vertical. Padrão da A1M.
- `back` põe a costura atrás (lado +Y da mesa). Bom quando a frente tem que ficar limpa.
- `random` espalha de propósito e é a causa mais comum de "pontinhos" (zits) nas paredes,
  segundo a Bambu. Use só em peça cilíndrica sem aresta, aceitando textura.
  [W](https://wiki.bambulab.com/en/knowledge-sharing/dots-on-the-print)
- Pintura de costura (Seam painting) na interface força a costura numa região.
- Cilindro não tem onde esconder costura: escolha `back`/`aligned` + scarf, ou posicione
  atrás da alça (alinhe a peça para a alça ficar em +Y).

## Paredes

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `wall_loops` | Loops de parede (Wall loops) | inteiro | 2 | Peça funcional: 3–4 (Prusa: resistência vem principalmente das paredes). Preset Strength usa 6. [PR](https://help.prusa3d.com/article/layers-and-perimeters_1748) |
| `wall_generator` | Gerador de parede | `classic` (Clássico), `arachne` (Aracne) | classic | `arachne` para texto pequeno, detalhes finos e paredes de espessura variável. Volte a `classic` se surgir costura ruim, parede solta ou superfície irregular. [W](https://wiki.bambulab.com/en/software/bambu-studio/wall-generator) |
| `wall_sequence` | Ordem das paredes (Order of walls) | `inner wall/outer wall`, `outer wall/inner wall`, `inner-outer-inner wall` | inner wall/outer wall | `outer wall/inner wall`: superfície externa mais limpa e (Prusa) mais precisão dimensional, pior em overhang. [W](https://wiki.bambulab.com/en/software/bambu-studio/parameter/quality-advance-settings) |
| `precise_outer_wall` | Parede precisa (Precise wall) | 0/1 | 0 | Encaixes e medidas externas críticas. [SRC] |
| `detect_thin_wall` | Detecte paredes finas | 0/1 | 0 | Com `classic`, salva detalhe mais fino que 2 linhas, com risco de linha solta. Prefira `arachne`. |
| `top_one_wall_type` | Apenas uma parede nas superfícies superiores | `not apply`, `all top`, `topmost` | all top | — |
| `ensure_vertical_shell_thickness` | Garanta a espessura vertical da casca | `disabled`, `partial`, `enabled` | enabled | Manter. |
| `detect_overhang_wall` | Detectar paredes salientes | 0/1 | 1 | Manter. |

## Topo e fundo (cascas)

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `top_shell_layers` | Camadas de casca superior | inteiro | 5 | Topo com "almofada"/furos (pillowing) ou preenchimento baixo: subir. |
| `top_shell_thickness` | Espessura da casca superior | mm | 1.0 | Mínimo garantido; camadas são somadas até atingir. |
| `bottom_shell_layers` | Camadas inferiores | inteiro | 3 | Fundo que precisa vedar (vaso, copo): 4–5. |
| `bottom_shell_thickness` | Espessura da camada inferior | mm | 0 (ignora) | — |
| `top_surface_pattern` | Padrão de superfície superior | `monotonicline`, `monotonic`, `concentric`, `zig-zag`, ... | monotonicline | `concentric` em tampa redonda; `monotonic` antes de ironing. |
| `bottom_surface_pattern` | Padrão de superfície inferior | idem | monotonic | — |
| `internal_solid_infill_pattern` | (Internal solid infill pattern) | idem | zig-zag | — |

Valores por preset A1M (topo/fundo): 0.08 → 9/7; 0.12 → 5/5; 0.16 → 6/4; 0.20 → 5/3; 0.24 e 0.28 → 4/3. [P]

## Preenchimento (infill)

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `sparse_infill_density` | Densidade de preenchimento esparsa | % | 15% | Prusa: 10–15% serve à maioria; raramente > 30%. Resistência: suba paredes antes. [PR](https://help.prusa3d.com/article/infill_42) |
| `sparse_infill_pattern` | Padrão de preenchimento esparso | ver lista | grid | Ver tabela abaixo. [W](https://wiki.bambulab.com/en/software/bambu-studio/fill-patterns) |
| `infill_wall_overlap` | Preenchimento/sobreposição de parede | % | 15% | — |
| `infill_direction` | (Infill direction) | graus | 45 | — |

Valores de `sparse_infill_pattern` e uso (Wiki Bambu):

| Valor | Interface | Uso |
| --- | --- | --- |
| `grid` | Grade | Padrão. Cruzamentos acumulam material: em alta velocidade o bico raspa. Evite em peça que empena |
| `gyroid` | Giroide | Resistência parecida em todas as direções, bom para peça grande/plana que empena (≤ 25%). Fatia mais devagar |
| `cubic` | Cúbico | Resistência uniforme X/Y/Z com bom custo |
| `adaptivecubic` | Cúbico adaptável | Mais denso perto das paredes e topo: economiza material em peça grande |
| `supportcubic` | (Support cubic) | Mais denso só perto do topo: economia em peça decorativa |
| `lightning` | A Iluminação | Só sustenta o topo. Apenas decorativo, sem carga |
| `tri-hexagon` | (Tri-hexagon) | Um dos mais fortes à tração |
| `honeycomb` / `3dhoneycomb` | Colmeia | Rígido e resistente a impacto, ~25% mais material e lento |
| `triangles` | (Triangles) | Bom ao cisalhamento; cruzamentos em densidade alta |
| `crosshatch` | (Cross hatch) | Rápido, baixa resistência |
| `zig-zag` | Retilíneo | Rápido; aceita 100% |
| `line` | Linha | Rápido |
| `concentric` | Concêntrico | Flexível (TPU) e filamento translúcido; aceita 100% |
| `alignedrectilinear` | (Aligned rectilinear) | Translúcido; topo pode cair se correr na mesma direção |
| `2dlattice` | (2D lattice) | Ângulo 0–45° favorece esmagamento vertical; 45–75° horizontal |
| `lockedzag` | (Locked zag) | Preenchimento que fica à vista |

100% de densidade: só `concentric`, `zig-zag`, `alignedrectilinear`, `hilbertcurve`,
`archimedeanchords`, `octagramspiral`.

## Precisão dimensional

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `elefant_foot_compensation` | Compensação do pé de elefante | mm | 0 (preset A1M) | Base alargada atrapalhando encaixe: calibrar (abaixo). Prusa: ~0.2 mm costuma servir. [W](https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot) |
| `xy_hole_compensation` | Compensação de furo X (X-Y hole compensation) | mm (+ abre o furo) | 0 | Furos saindo apertados de forma consistente. Prefira corrigir no modelo com folga explícita. |
| `xy_contour_compensation` | Compensação de contorno XY | mm (− encolhe) | 0 | Contorno externo saindo grande. |
| `resolution` | (Resolution) | mm | 0.012 | — |

Calibrar pé de elefante: imprimir cubo 25x25x10 com compensação 0 e sem brim; valor =
(excesso em X + excesso em Y) / 2. Repetir ao trocar de placa. [W](https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot)

## Aderência e primeira camada

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `brim_type` | Tipo de brim | `auto_brim` (Automático), `brim_ears` (Pintado / orelhas), `outer_only` (Apenas brim externo), `inner_only`, `outer_and_inner`, `no_brim` (Sem Brim) | auto_brim | Cantos levantando: `outer_only` com largura 8–10 mm. Peça alta e fina: brim. [W](https://wiki.bambulab.com/en/software/bambu-studio/auto-brim) |
| `brim_width` | Largura do brim | mm | 5 | 8–10 contra empeno. [W](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/warping-falling-off-collapsing) |
| `brim_object_gap` | Lacuna Brim-object | mm | 0.1 | Brim difícil de soltar: 0.15–0.2. |
| `raft_layers` | Camadas de Raft | inteiro | 0 | Quase nunca na PEI texturizada. |
| `skirt_loops` | Voltas da saia | inteiro | 0 | — |
| `textured_plate_temp` / `textured_plate_temp_initial_layer` | (filamento) temperatura da placa texturizada | °C | 65 / 65 | PLA na PEI texturizada: 55–65; +5–10 se empenar. [W](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/warping-falling-off-collapsing) |

Placa: o tipo no fatiador precisa ser o real (`--placa`). PEI texturizada não precisa de
cola com PLA/PETG/TPU; esperar esfriar para tirar a peça; limpar com água morna e detergente
sem hidratante, nunca acetona. [W](https://wiki.bambulab.com/en/filament-acc/acc/pei-plate-clean-guide)

## Suporte

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `enable_support` | Habilitar suporte | 0/1 | 0 | Overhang < 45° do plano da mesa que o modelo não resolve. |
| `support_type` | Tipo | `normal(auto)`, `tree(auto)`, `normal(manual)`, `tree(manual)` | tree(auto) | `normal` para overhang grande e plano; `tree` para pequeno/complexo/orgânico. `manual` = só onde pintado. [W](https://wiki.bambulab.com/en/software/bambu-studio/support) |
| `support_style` | Estilo | `default`, `grid`, `snug`, `tree_slim`, `tree_strong`, `tree_hybrid`, `tree_organic` | default (= orgânico) | — |
| `support_threshold_angle` | Ângulo limite | graus | 30 | Maior = mais suporte. Presets: 15° (0.08) a 40° (0.28). |
| `support_on_build_plate_only` | Somente na placa de construção | 0/1 | 0 | Evita marcas de suporte sobre a peça. |
| `support_top_z_distance` | Distância Z superior | mm | 0.2 | Maior = sai fácil, superfície pior. |
| `support_interface_top_layers` | Camadas superiores da interface | inteiro | 2 | 3 = base mais plana sob a peça. |
| `support_object_xy_distance` | (Support/object xy distance) | mm | 0.35 | — |
| `max_bridge_length` | (Max bridge length, tree) | mm | 0 (= suporta toda ponte) | Pontes curtas sem suporte: 10. |

## Overhang e ponte

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `enable_overhang_speed` | Desacelere para saliências | 0/1 | 1 | Manter. Velocidades por fração em balanço: 0/50/30/10/10 mm/s. [W](https://wiki.bambulab.com/en/software/bambu-studio/slow-down-for-overhang) |
| `overhang_fan_speed` | (filamento) | % | 100 | Manter 100 em PLA. |
| `bridge_flow` | Fluxo da ponte | fator | 1 | Ponte caindo: teste 1.4–1.7 em PLA (teste da comunidade adotado pela Bambu). [W](https://wiki.bambulab.com/en/software/bambu-studio/parameter/bridge) |
| `bridge_speed` | (Bridge speed) | mm/s | 50 | Ponte ruim: 10–50. |
| `thick_bridges` | Pontes grossas | 0/1 | 0 | Pontes externas mais robustas. |

Bambu Studio NÃO tem "make overhang printable" (é do OrcaSlicer). Resolva no modelo
(chanfro 45°, furo em gota).

## Passar a ferro (ironing)

| Chave | Interface | Valores | Padrão | Quando mudar |
| --- | --- | --- | --- | --- |
| `ironing_type` | Tipo de engomar | `no ironing`, `top`, `topmost`, `solid` | no ironing | Topo plano que precisa ficar liso (placa de nome, tampa, superfície a colar). Não usar em superfície orgânica. [W](https://wiki.bambulab.com/en/software/bambu-studio/parameter/ironing) |
| `ironing_flow` | (Ironing flow) | % | 10% | — |
| `ironing_spacing` | (Ironing line spacing) | mm | 0.15 | Menor que o bico. |
| `ironing_speed` | (Ironing speed) | mm/s | 30 | — |

Custos: mais tempo; risco de entupimento por heat creep com PLA/PETG/TPU; pode soltar
peça mal aderida. Combine com `top_surface_pattern=monotonic`.

## Modos especiais

| Chave | Interface | Valores | Padrão | Uso |
| --- | --- | --- | --- | --- |
| `spiral_mode` | Vaso em espiral | 0/1 | 0 | Vaso/cachepô de parede única, sem costura. Peça sem topo e sem recursos internos |
| `fuzzy_skin` | Pele felpuda | `none`, `external`, `all`, `allwalls` | none | Textura áspera que esconde camadas e costura (pega mão) |
| `print_sequence` | Sequência de impressão | `by layer`, `by object` | by layer | `by object`: várias peças pequenas, uma de cada vez (atenção à altura do bico) |
| `enable_arc_fitting` | Ajuste de arco | 0/1 | 1 | Malha escaneada/irregular: desligar. [W](https://wiki.bambulab.com/en/software/bambu-studio/fix-model) |

## Filamento (Bambu PLA Basic @BBL A1M)

| Chave | Interface | Padrão | Nota |
| --- | --- | --- | --- |
| `nozzle_temperature` / `nozzle_temperature_initial_layer` | Temperatura do bocal | 220 / 220 | Faixa do filamento 190–240. Overhang melhora com ~205 °C. [W](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/overhang) |
| `filament_flow_ratio` | Relação de fluxo | 0.98 | Calibrar por marca. |
| `filament_max_volumetric_speed` | Velocidade volumétrica máxima | 21 mm³/s | Limite real de velocidade. |
| `fan_min_speed` / `fan_max_speed` | — | 60 / 80 % | — |
| `slow_down_layer_time` | Impressão lenta para melhor resfriamento da camada | 6 s | Peça pequena/fina derretendo no topo: subir para 8–10. |
| `temperature_vitrification` | — | 45 °C | Temperatura de amolecimento usada pelo fatiador. |

## Máquina (A1 mini 0.4)

`retraction_length` 0.8 mm, `retraction_speed` 30, `z_hop` 0.4 (`z_hop_types` Auto Lift),
`wipe` 1 (2 mm). Fios (stringing): secar filamento, retração ≤ 2 mm, "Evite cruzar a
parede" (`reduce_crossing_wall=1`), baixar temperatura. [W](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/stringing-oozing)
