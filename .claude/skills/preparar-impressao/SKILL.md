---
name: preparar-impressao
description: Prepara peças para imprimir na Bambu Lab A1 mini — checa imprimibilidade (malha fechada, tamanho, overhang, área na mesa), escolhe orientação, filamento e processo, fatia pelo CLI do Bambu Studio, informa tempo e gramas e abre o projeto 3MF no Bambu Studio. Use quando o usuário pedir para "fatiar", "preparar para imprimir", "quanto tempo/filamento", "mandar pro Bambu", ou ao finalizar um modelo.
---

# Preparar impressão (A1 mini)

## 1. Checar a peça

Se ainda não houver `saida/relatorio.json` atualizado, gere:

```bash
tools/blender.sh projetos/<nome>/modelo.py            # modelo do repositório
tools/blender.sh tools/inspecionar.py -- arquivo.stl  # STL de fora (ex.: baixado)
```

Leia o relatório e a folha de previews. Interprete:

| Campo | Ação |
| --- | --- |
| `malha_fechada: false` / `bordas_abertas` > 0 | Buraco na malha. Corrigir no modelo (booleanas, `malha.limpar`). Não fatie assim: o fatiador fecha errado, pula camadas ou deixa vão |
| `arestas_com_3_ou_mais_faces` > 0 | Faces grudadas em aresta (não-manifold). Refazer a união com `malha.booleana(..., "UNION")` |
| `autointersecoes` > 0 | Partes atravessando outras sem união. Trocar `malha.juntar` por `malha.booleana(..., "UNION")` |
| `ilhas_flutuando` > 0 | Parte solta no ar: vai virar espaguete. Encostar na peça ou na mesa |
| `ilhas` > 1 | Várias partes num objeto. Ok se intencional (ex.: peças lado a lado); senão unir |
| `faces_degeneradas` > 0 | `malha.limpar(obj)` |
| `volume_cm3` negativo | Normais invertidas: `malha.limpar(obj)` |
| `area_abaixo_detalhe_min_pct` > 0.5 | Detalhes < 0.8 mm (2 linhas): engrossar, aumentar escala ou camada/linha mais fina. `espessura_p5_mm` mostra a espessura típica das partes finas |
| `area_abaixo_parede_min_pct` > 5 | Paredes < 1.2 mm: fracas e com vãos entre linhas. Engrossar ou aceitar com o usuário |
| `z_min_mm` ≠ 0 | `malha.apoiar_na_mesa(obj)` |
| `cabe_na_mesa: false` | Reorientar, reduzir ou dividir a peça |
| `area_contato_mesa_mm2` < 50 | Reorientar, adicionar aba (brim) ou base de sacrifício |
| `area_overhang_mm2` > 0 | Reorientar, chanfrar a 45° ou aceitar suporte |

`espessura_min_mm` é o menor valor amostrado e pode ser ruído de borda; decida pelos
percentuais e pelo `espessura_p5_mm`.

## 2. Orientação

- Maior face plana na mesa.
- Faces à vista para cima ou de lado (a face na mesa fica com textura da placa PEI).
- Esforço mecânico ao longo das camadas, nunca separando camadas.
- Furos com precisão: eixo vertical (furo horizontal sai oval).
- Objetos de revolução (canecas, copos): boca para cima.

Modele já na orientação final. Se precisar girar só para imprimir, faça no `modelo.py`
e registre no README.

## 3. Escolher presets e ajustes

Carregue a skill `configuracao-impressao`: ela define perfil por tipo de peça, costura,
paredes, cascas, preenchimento, suporte e aderência, e as chaves para `--ajuste`.
Nunca fatie peça final só com o preset padrão sem decidir a costura.

Padrões em `config/impressora.json`. Liste os disponíveis:

```bash
python3 tools/fatiar.py --listar processo
python3 tools/fatiar.py --listar filamento | grep -i "PLA\|PETG"
```

| Situação | Processo |
| --- | --- |
| Geral | `0.20mm Standard @BBL A1M` |
| Detalhe fino, texto pequeno, relevo de logo | `0.12mm Fine @BBL A1M` ou `0.16mm Optimal @BBL A1M` |
| Peça mecânica resistente | `0.20mm Strength @BBL A1M` |
| Rascunho rápido | `0.28mm Extra Draft @BBL A1M` |

Filamento: PLA Basic é o padrão. PETG para calor/umidade/flexão leve.

## 4. Fatiar

```bash
python3 tools/fatiar.py projetos/<nome>/saida/<peça>.stl
python3 tools/fatiar.py projetos/<nome>/saida/a.stl projetos/<nome>/saida/b.stl --nome conjunto
python3 tools/fatiar.py peca.stl --processo "0.12mm Fine @BBL A1M" --filamento "Bambu PETG Basic @BBL A1M"
python3 tools/fatiar.py peca.stl --ajuste seam_position=back --ajuste seam_slope_type=external \
  --ajuste wall_loops=4 --ajuste sparse_infill_pattern=gyroid --ajuste sparse_infill_density=20%
```

Cada `--ajuste` é conferido no G-code (`ajustes.<chave>.ok`). Ajuste não aplicado aparece
em `erros_cli`: chave ou valor inválido, corrija.

Opções úteis: `--orientar` (Bambu escolhe orientação), `--sem-arranjo` (mantém posições
relativas; a origem do modelo vai para o centro da mesa), `--so-3mf` (projeto sem fatiar),
`--multicor` (ver abaixo), `--saida pasta`.

Saída em `projetos/<nome>/saida/fatiado/`: `<nome>.3mf` (projeto com G-code embutido),
`plate_1.gcode`, `result.json`. O script imprime um JSON com tempo, gramas, metros e
avisos. `ok: false` ou `erros_cli` não vazio: investigue antes de seguir.

O aviso `glfwInit` / `Failed to connect to display` só afeta a miniatura; pode ignorar.

## 5. Entregar ao usuário

O 3MF do CLI precisa de `different_settings_to_system` preenchido, senão a interface do Bambu
mostra o perfil de sistema e perde os ajustes ao fatiar de novo. `fatiar.py` e `mesas.py` já
fazem; em 3MF montado por outro script, rode `python3 tools/marcar_ajustes_3mf.py <3mf>` por
último (depois de gravar pintura ou copiar G-code).

1. Informe: tempo estimado, gramas, processo e filamento usados, avisos.
2. Abra no Bambu Studio para revisão e envio à impressora:
   ```bash
   bambu-studio "projetos/<nome>/saida/fatiado/<nome>.3mf" >/dev/null 2>&1 &
   ```
3. Atualize a tabela "Impressão" no README do projeto.

O Claude não envia para a impressora. O usuário revisa e imprime pelo Bambu Studio.

## Multicor

A1 mini com AMS lite aceita até 4 filamentos. Antes de planejar multicor, pergunte se o
usuário tem AMS lite. Caminhos:

- Com AMS lite: exporte um STL por cor (mesma origem, sem UNION entre as cores) e rode
  ```bash
  python3 tools/fatiar.py base.stl logo.stl --nome placa --multicor \
    --filamento "Bambu PLA Basic @BBL A1M" --filamento "Bambu PLA Matte @BBL A1M"
  ```
  Gera um 3MF com um objeto e uma parte por STL, cada parte no seu filamento
  (`--ids-filamento 1,2,1` para mapear diferente). O CLI do Bambu não faz troca de cor
  ao fatiar (testado na 02.08): o 3MF sai SEM G-code. Abra no Bambu Studio, confira as
  cores e fatie lá. Avise o usuário que tempo e peso só aparecem depois disso.
- Com AMS lite, peça orgânica (rosto, cabelo, barba): pintura por triângulo em vez de
  partes. `tools/bl/pintura.py` grava um 3MF com `paint_color` (cor) e `paint_supports`
  (forçar/bloquear suporte), o mesmo dado das ferramentas de pintura do Bambu. Esse 3MF o
  CLI fatia COM troca de cor:
  ```bash
  python3 tools/fatiar.py peca_pintada.3mf --sem-arranjo --filamento A --filamento B ... \
    --cores "#D4A385,#101010,..." [--torre 130,110]
  ```
  Sem `--cores` (um `filament_colour` por filamento) o CLI 02.08 dá segfault; sem torre
  dentro da mesa dá "gcode unprintable". Testado em projetos/cabeca-homem-realista.
  Custo: cada camada com 2+ cores troca filamento (~280 mm³ de purga por troca). Cabeça de
  38 mm em 0.12 com 4 cores: 356 trocas, 12h19, 130 g para uma peça de 9 g. Informe antes.
  A pintura (Bambu ou Blender) NÃO mostra o que imprime: o fatiador junta cores e vãos
  menores que a linha do bico (~0,45 mm no 0.4). Textura fina (barba rala, pontilhado) que
  parecia em traços saiu quase cheia. Confira pelo G-code e mostre isso ao usuário:
  `python3 tools/gcode_frente.py plate_1.gcode rosto.png --cores "#..,#.."` (paredes externas
  vistas de frente, por filamento). A ferramenta lê os arcos `G2`/`G3` (o Bambu liga
  `enable_arc_fitting`); antes de 2026-11-11 ela os ignorava e mostrava "riscos" de perímetros
  internos de outra cor onde a parede da frente era arco.
- Detalhe de cor pequeno (dentes, letras) NÃO combina com relevo: o fatiador reparte cada camada
  pela superfície pintada mais próxima, e as paredinhas de um ressalto/rebaixo de outra cor
  tomam o miolo do detalhe. Dentes de 1,3 mm com vão afundado 0,4 mm imprimiram com 15–40% da
  largura; só pintura (superfície lisa) saiu legível (projetos/Asta). Se o relevo for
  obrigatório, pinte as paredinhas pelo centro do triângulo (meio a meio) e confira no G-code.
  Detalhe de cor fica legível a partir de ~1 mm de largura por camada; ponta de triângulo some.
- Reaproveitar purga no A1 mini (testado em 2026-11-11, projetos/jacare-chef): a troca de cor
  faz a purga INTEIRA na calha pelo G-code da máquina (volume da tabela, ex.: preto→branco
  553 mm³). "Purgar neste objeto"/"no preenchimento" só descontam o que a peça imprime logo após
  a troca naquela camada (dezenas de mm³): 239 trocas, calha 96,6 → 91,5 g com um objeto de
  purga de 98 mm a 30%. Sem torre, nem isso. O objeto de purga também não é impresso sempre
  primeiro depois da troca (ordem por percurso), então não limpa o bico como a torre. A torre
  sobe até a peça mais alta da mesa. O que reduz purga de verdade: `flush_multiplier` (0,8 deu
  −16 g, 0,7 −24 g numa figura de 155 g) ou menos trocas. Medir gramas da calha: somar E dentro
  dos blocos `M620 S`…`M621 S` do G-code.
- Sem AMS: troca manual por altura (pausa na camada). Planeje o relevo com altura
  múltipla da camada (ex.: 0.2 mm) e informe ao usuário em qual altura trocar.

## Projeto com várias mesas (entrega com peças já arrumadas)

Para entregar um 3MF com várias mesas, cada peça com posição, filamento e ajustes próprios,
use `--load-assemble-list` do CLI. Peças de uma cor (sem objeto montado): `tools/mesas.py` →
`montar(saida, nome, mesas, maquina, processo, filamentos)` (centra cada STL pela caixa e
confere a linha `;===== machine:` no G-code); exemplos em `projetos/*/montar_mesas.py`
(escorredor, lixeira, dispenser, na A1 de 256 mm). Outra impressora num projeto só: passe
`maquina`/`processo`/`filamentos` da A1 (`... @BBL A1`) sem mudar `config/impressora.json`. Exemplo pronto: `projetos/caneca-jo-spinola/montar_mesas.py`
(reaproveita `indexar_presets`/`resolver`/`achar_bambu` do `tools/fatiar.py`). Formato:

```json
{"plates": [{"plate_name": "1 - silk", "need_arrange": false, "objects": [
  {"path": "/abs/caneca.stl", "count": 1, "filaments": [1], "assemble_index": [0],
   "pos_x": [62.0], "pos_y": [90.0], "pos_z": [0.0], "print_params": {"wall_loops": "6"}}]}]}
```

Antes de entregar qualquer G-code/3MF, confira que é o G-code da máquina e não o genérico:
`grep -m1 ";===== machine: A1 mini" plate_1.gcode` tem que achar a linha (ver `include` no
`CLAUDE.md`, "Bambu Studio CLI — armadilhas").

Testado na 02.08 (2026-10-17):
- `need_arrange` precisa ser booleano: com `0` dá "type must be boolean".
- `pos_x`/`pos_y`/`pos_z` são somados à ORIGEM do STL (testado em 2026-10-25): só viram o
  centro do bbox na mesa se o STL estiver centrado na origem em XY e com o fundo em z = 0.
  STL deslocado (ex.: partes de um grupo multicor exportadas juntas): use
  pos = centro desejado − centro do bbox do STL, `pos_z` = 0. Partes de um objeto montado
  recebem a mesma posição (ficam no lugar relativo dos STLs). Erro típico quando isso falha:
  "Found Object assemble_1 partly inside, can not be sliced". Exemplo:
  `posicoes()` em `projetos/suporte-alexa-ghost-busters/montar_mesas.py`.
- Altura de camada por objeto funciona em `print_params` (`layer_height`), por mesa ou peça.
  Peças de 0,20 com objeto multicor de 0,12 na mesma entrega: processo base = o do objeto
  montado, e `layer_height` + ajustes nas peças sozinhas.
- `assemble_index` 0 = peça sozinha. O mesmo índice ≥ 1 junta as peças num objeto de
  várias partes (multicor), e cada parte fica com seu filamento. O objeto montado sai com o
  nome `assemble_N` e PERDE os `print_params`: ponha esses ajustes no processo ou renomeie e
  ajuste depois.
- Com a lista de montagem, o CLI fatia a mesa multicor (com trocas de cor e torre de purga),
  ao contrário do `--multicor` do `fatiar.py`.
- A torre de purga padrão (15, 220) cai fora da mesa da A1 mini e o fatiamento falha com
  "G-code outside of the printable area". Defina `wipe_tower_x`/`wipe_tower_y` no processo
  (lista com um valor por mesa). A torre ocupa ~(x-3, y-3) a (x+50, y+50).
- Ao abrir o 3MF, o Bambu apoia cada OBJETO na mesa (z = 0). Peças de uma figura montada
  (mostruário) como objetos soltos caem todas para a mesa e se sobrepõem: junte-as num objeto de
  várias partes (`assemble_index` >= 1; em `tools/mesas.py`, 6º elemento do item = grupo).
- `--load-assemble-list` não aceita 3MF ("unsupported file"). Para peças pintadas: monte com os
  STLs e grave a pintura depois nos `<triangle>` do 3MF (o Bambu mantém a ordem dos triângulos
  do STL). Exemplo: `projetos/homem-realista/montar_mesas.py`.
- Uma mesa mais alta que o volume (mostruário) faz `--slice 0` falhar em todas. `--slice N`
  fatia só a mesa N, mas o 3MF exportado sai só com os objetos dela: fatie cada mesa a partir
  do mesmo 3MF e copie `Metadata/plate_N.gcode` (+ .md5, .json, bloco do slice_info.config e
  `gcode_file` no model_settings.config) para o 3MF completo. Mesmo exemplo.
- O cabeçalho do G-code sai sem peso quando há vários filamentos; leia
  `result.json` → `sliced_plates[].filaments[].total_used_g`.

