# Projetos 3D — Blender + Bambu Studio

Repositório de modelagem 3D para impressão. O Claude modela peças com scripts Python
no Blender (bpy), confere o resultado por imagens renderizadas e relatório de malha, e
fatia no Bambu Studio. O usuário revisa e imprime pelo Bambu Studio.

Idioma: português (código, nomes de arquivos, docs e respostas).

## Ambiente desta máquina

| Item | Valor |
| --- | --- |
| Blender | 5.2.2 LTS, comando `blender` (snap). Python 3.13, numpy incluso, sem Pillow |
| Bambu Studio | 02.08, comando `bambu-studio` (wrapper de AppImage em `~/.local/bin`) |
| Impressora | Bambu Lab A1 mini, bico 0.4 mm, volume 180 x 180 x 180 mm, placa Textured PEI |
| Filamento padrão | Bambu PLA Basic |
| Python do sistema | `python3` com Pillow e numpy (usado por `tools/fatiar.py` e `tools/imagem_para_svg.py`) |

Configuração da impressora e regras de projeto: [config/impressora.json](config/impressora.json).
Se trocar impressora, bico ou filamento padrão, altere só esse arquivo.

## Estrutura

```
CLAUDE.md                  este arquivo
iniciar.sh / iniciar.bat   abre a Oficina 3D (interface web local) no Linux / Windows
app/                       Oficina 3D: servidor Node (Agent SDK) + interface em app/publico
config/impressora.json     impressora, presets padrão do Bambu, regras de projeto (mm)
.claude/skills/            skills do Claude para este repo (ver lista abaixo)
tools/
  blender.sh               roda script bpy headless (tools/ no sys.path)
  bl/                      biblioteca para scripts bpy: cena, formas, malha, exportar, checagem, preview, logo,
                           contorno (potes/cestos com estrias), cotas (folha de medidas)
  inspecionar.py           relatório + previews de qualquer STL/OBJ/PLY/3MF/.blend
  cortar_stl.py            cortes de um STL (contornos e PNG) para medir peças de terceiros
  fatiar.py                fatia no Bambu Studio via CLI (resolve herança de presets)
  mesas.py                 3MF de entrega com várias mesas arrumadas (--load-assemble-list)
  gcode_frente.py          imagem de frente do G-code por filamento (multicor como sai impresso)
  desenhar_cotas.py        desenha as cotas da folha de medidas (Pillow), chamado por bl/cotas.py
  imagem_para_svg.py       imagem/logo -> SVG para relevo
  novo_projeto.sh          cria projeto a partir de projetos/_modelo
  blender_ponte/           ponte para controlar o Blender aberto (modo ao vivo)
projetos/
  _modelo/                 modelo de projeto (não editar para um projeto real)
  <nome-do-projeto>/
    README.md              requisitos, decisões, parâmetros de impressão, histórico
    modelo.py              script paramétrico: FONTE DA VERDADE da geometria
    referencias/           fotos, desenhos, logos, STLs de terceiros (não alterar)
    saida/                 gerado: <peça>.stl, modelo.blend, relatorio.json, preview/, fatiado/
```

## Fluxo de um projeto

O fluxo completo, com portões de aprovação e quando abrir cada ferramenta, está na skill
`fluxo-projeto`. Carregue-a ao começar ou retomar qualquer projeto. Resumo:

```
F0 Entrada → F1 Sabatina ⛔ → F2 Modelagem por etapas ⛔⛔⛔ → F3 Peça de teste ⛔ → F4 Fatiar e entregar ⛔ → F5 Pós-impressão
```

Regras que valem sempre:

- **Sabatina antes de modelar.** Projeto novo ou referência nova: skill `grill-me`. Nada de
  `modelo.py`, Blender ou fatiamento até a especificação estar aprovada pelo usuário.
- **Portões (⛔) exigem "sim" explícito.** Pergunte com `AskUserQuestion`.
- **Retomar = ler o README do projeto.** O campo Status diz a fase; a Especificação diz o
  combinado. Não repita perguntas respondidas.
- **Informação nova que muda requisito** reabre a sabatina só naquele galho.
- **Nunca declare um modelo pronto** sem ter lido `saida/preview/folha.png` e
  `saida/relatorio.json` e feito a autorrevisão da skill `fluxo-projeto`.

## Oficina 3D (interface visual)

`app/` é uma interface web local para quem não usa VS Code. Ela cria o projeto (F0), copia o
`.3mf` da IA e as imagens para `referencias/` e abre uma sessão do Claude (Agent SDK) com
`settingSources: ["project"]`: este CLAUDE.md e as skills valem igual. Diferenças quando o
prompt de sistema disser que você está na Oficina:

- A pessoa não vê terminal. Toda pergunta e portão: `AskUserQuestion` (vira botões).
- Imagem que você lê (Read) dentro de `projetos/<nome>/` aparece para a pessoa. Leia a folha
  de previews antes de pedir aprovação.
- A interface tem botões "Abrir no Bambu Studio" (todo `.3mf` em `saida/` e `saida/fatiado/`)
  e "Abrir no Blender" (`saida/modelo.blend`).
- Windows: o Bash é o Git Bash. `blender`, `bambu-studio` e `python3` vêm de atalhos em
  `app/.atalhos/` (no PATH da sessão); `BLENDER` e `BAMBU_STUDIO` também ficam definidos.

## Integração com o Blender — três modos

**1. Headless (padrão).** Para gerar, exportar, checar e renderizar.
```bash
tools/blender.sh projetos/<nome>/modelo.py
tools/blender.sh tools/inspecionar.py -- arquivo.stl [--saida pasta]
tools/blender.sh /caminho/script_qualquer.py -- args
```
Roda com `--factory-startup` (sem add-ons do usuário), sai com código 1 em exceção.
Saída longa: filtre com `2>&1 | grep -vE "render +\| Saved|^$"` ou procure `RELATORIO_JSON`.

**2. Ao vivo (Blender aberto pelo usuário).** Use quando o usuário estiver com o Blender
aberto e quiser ver as mudanças acontecendo ou pedir algo sobre a cena atual.
Skill `blender-ao-vivo`. Resumo:
```bash
python3 tools/blender_ponte/cliente.py --status
python3 tools/blender_ponte/cliente.py -c "print(bpy.context.selected_objects)"
python3 tools/blender_ponte/cliente.py projetos/<nome>/modelo.py
python3 tools/blender_ponte/cliente.py --captura /tmp/viewport.png   # depois: Read na imagem
```
`modelo.py` chama `cena.nova_cena()`, que APAGA os objetos da cena aberta. Confirme com o
usuário antes de rodar um modelo na sessão ao vivo se a cena tiver trabalho não salvo.

**3. Abrir para o usuário.** Para o usuário inspecionar ou editar à mão:
`blender "projetos/<nome>/saida/modelo.blend" >/dev/null 2>&1 &`
Edições manuais no .blend não voltam para o `modelo.py`. Se o usuário editar à mão,
pergunte se o .blend passa a ser a fonte da verdade e registre no README.

## Convenções de modelagem

- 1 unidade do Blender = 1 mm (`cena.nova_cena()` já configura). STL sai em mm.
- Z para cima. Peça apoiada em Z = 0 e centrada em XY (`malha.apoiar_na_mesa`).
- Modele já na orientação de impressão, salvo quando o README disser outra coisa.
- Parâmetros em MAIÚSCULAS no topo do `modelo.py`, com unidade no nome ou comentário.
- Nome do objeto = nome do STL. Use nomes curtos em kebab/snake case sem acento.
- Uma peça por objeto. Peças separadas viram STLs separados (`exportar.stl_por_peca`).
- Não edite STL gerado à mão. Mude o `modelo.py` e gere de novo.
- Não altere nada em `referencias/`. Copie para `saida/` se precisar transformar.

## Regras de imprimibilidade (A1 mini, bico 0.4, PLA)

Valores em `config/impressora.json` → `projeto`. Resumo:

- Parede mínima 1.2 mm (3 linhas). Detalhe mínimo 0.8 mm.
- Folga de encaixe: 0.2 mm justo, 0.4 mm solto (por lado).
- Overhang até 45° sem suporte. Pontes até ~10 mm.
- Texto/relevo: altura ≥ 0.6 mm, letra ≥ 4 mm de altura.
- Volume útil 180 x 180 x 180 mm, com 5 mm de margem na mesa.
- Prefira chanfro de 45° a filete nas bordas de baixo (evita overhang e pé de elefante).
- Furos horizontais: use formato gota ou topo chanfrado para não precisar de suporte.
- Furos saem ~0.2–0.25 mm menores que no modelo. Inserto M3 de latão: furo 4.2 mm,
  parede ≥ 1.6 mm, furo cego 1 mm mais fundo que o inserto.
- Encaixe crítico: valide com peça de teste no mesmo processo/filamento da peça final.
- Costura: decida sempre. Nunca `nearest`/`random` em peça redonda (ver skill
  `configuracao-impressao`; testado nesta máquina).
- Fontes e números por trás dessas regras: `.claude/skills/configuracao-impressao/conhecimento.md`.

## API do Blender 5.x — armadilhas conhecidas

- Exportar/importar STL: `bpy.ops.wm.stl_export` / `bpy.ops.wm.stl_import`
  (`bpy.ops.export_mesh.stl` não existe mais). Use `tools/bl/exportar.py`.
- Importar SVG: `bpy.ops.import_curve.svg`. Curva 2D não aceita `transform_apply`:
  converta para malha antes de escalar (`tools/bl/logo.py` já faz).
- Booleanas: use sempre `malha.booleana(alvo, ferramenta, "DIFFERENCE")`. Ela tenta os
  solvers MANIFOLD, FLOAT e EXACT e fica com o primeiro resultado sem arestas abertas nem
  triângulos cruzados. Nenhum solver acertou todos os casos nos testes (MANIFOLD cruzou
  triângulos ao unir logo em cilindro; EXACT abriu arestas com logo plano).
- Booleana pode "dar certo" sem cortar: um solver devolveu a malha intacta, sem aresta aberta nem
  cruzamento. `malha.booleana` agora confere, na DIFFERENCE, se sobrou vértice do alvo dentro da
  ferramenta (amostra, voto de 3 raios) e descarta esse resultado. Mesmo assim, confira o
  volume ou a imagem depois de cortes grandes.
- UNION com MANIFOLD em malha que tem aresta de 4 faces (ou que se cruza) pode devolver só a
  ferramenta, e `malha.booleana` aceita como "limpo" (a conferência de corte vale só para
  DIFFERENCE). Aconteceu com `malha.fechar_pincamentos` depois de uma união EXACT. Para malha
  orgânica que se cruza (dedos inflados), use o modificador BOOLEAN com `solver="EXACT"` e
  `use_self=True` (ver `resolver_autointersecoes` em projetos/suporte-alexa-ghost-busters) e
  confira o volume depois.
- `malha_fechada: true` não basta: malha fechada pode ter triângulos se cruzando. O
  relatório traz `autointersecoes`, `ilhas_flutuando` e espessura por raycast.
- STL com "manifold = no" no Bambu e malha fechada no Blender: o exportador triangula
  n-gonos côncavos de booleanas do jeito dele e cria arestas com 4 faces, ou duas partes se
  tocam só numa aresta ("gravata"). `exportar.stl` já triangula antes (BEAUTY), e o
  relatório traz `nao_manifold_apos_soldar` (solda vértices como o fatiador faz). Para
  conferir o que o Bambu vê: `bambu-studio --info arquivo.3mf` (campo `manifold`).
- Superfície plana curvada por script (ex.: `logo.enrolar_em_cilindro`) precisa ser
  triangulada ANTES de curvar; n-gono não-planar vira faces dobradas no STL.
- UNION de peças que se encostam face a face (ex.: partes de cor de um multicor) pode
  derrubar o Blender (aconteceu na sessão ao vivo). Para versão de uma cor, reconstrua a peça
  com sobreposição real (ex.: gomos entrando 0,3 mm no corpo) em vez de unir as partes de cor.
  Teste booleanas arriscadas no headless antes de rodar na ponte ao vivo.
- Formas de `bl.formas` e `bl.logo` saem com transformação zerada: `obj.location.z += 3`
  desloca a partir da posição criada.
- Render Workbench com fundo branco sai cinza com o view transform padrão (AgX): use
  `view_settings.view_transform = "Standard"` (`bl/cotas.py` já faz).
- Operadores que dependem de janela (viewport, screenshot) só funcionam no modo ao vivo,
  com `bpy.context.temp_override(window=..., area=..., region=...)`.
- Em `-b` (headless) `bpy.app.timers` não roda. Execute tudo em sequência.
- Prefira `bmesh` e dados diretos (`obj.data`) a `bpy.ops` dentro de laços: é mais rápido
  e não depende de contexto.
- `bmesh.ops.subdivide_edges` em parte de uma malha triangulada, repetido, criou arestas com 4
  faces (não-manifold). Para refinar uma região, use o corte em numpy de projetos/Asta
  (`_subdividir`) e confira `nao_manifold_apos_soldar`.

## Bambu Studio CLI — armadilhas conhecidas

- Presets da 02.08 usam `inherits` E `include`: o G-code de início/fim/troca de filamento/
  timelapse da A1 mini vem de templates `include`. Sem seguir `include`, o CLI fatia com o
  G-code genérico do `fdm_machine_common` (purga em Y200, fora da mesa de 180; sem nivelamento
  nem AMS). `tools/fatiar.py` → `resolver` já trata. Confira no G-code: a linha
  `;===== machine: A1 mini` tem que aparecer.
- Torre de purga padrão (15, 220) fica fora da mesa da A1 mini: defina `wipe_tower_x/y`.
- Ao abrir um 3MF, o Bambu apoia cada objeto na mesa (z = 0): figura montada para mostruário
  tem de ser UM objeto de várias partes, não objetos soltos (ver skill `preparar-impressao`).
- Abrir no Bambu Studio para o usuário: passe o caminho ABSOLUTO do 3MF. O app muda a pasta
  de trabalho para `~/.config/BambuStudio/log` e um caminho relativo abre a janela vazia.
- 3MF gerado pelo CLI sai com `different_settings_to_system` vazio: a interface do Bambu abre com
  os valores do PERFIL DE SISTEMA (no Asta: 2 paredes, sem suporte, torre ligada) e fatiar de
  novo lá perde os ajustes. `tools/fatiar.py` e `tools/mesas.py` já chamam
  `tools/marcar_ajustes_3mf.py`; 3MF montado à mão: rode `python3 tools/marcar_ajustes_3mf.py x.3mf`.
- 3MF com pintura de cor (`paint_color`): o CLI 02.08 dá segfault ao fatiar se cada filamento
  não tiver `filament_colour` próprio. `tools/fatiar.py --cores` resolve (e põe a torre em
  `--torre`, padrão 130,110). Com isso o CLI fatia com troca de cor de verdade.
- Raycast de uma vista para marcar pontos na malha (linha do cabelo etc.): o raio bate na
  primeira superfície, que pode não ser a esperada (têmpora em vez de testa, atrás da
  orelha em vez da nuca). Imprima a tabela de pontos convertidos e procure valores fora de ordem.

## Skills deste repositório

Em `.claude/skills/`. Carregue a skill quando a tarefa casar com a descrição.

| Skill | Quando usar |
| --- | --- |
| `fluxo-projeto` | Começar ou retomar um projeto; saber a próxima fase e qual ferramenta abrir |
| `grill-me` | Sabatina: levantar todos os requisitos antes de modelar |
| `modelagem-blender` | Escrever ou alterar `modelo.py` (receitas bpy) |
| `blender-ao-vivo` | Trabalhar no Blender aberto pelo usuário (ponte) |
| `preparar-impressao` | Checar imprimibilidade, orientar, fatiar, abrir no Bambu Studio |
| `configuracao-impressao` | Costura, camadas, paredes, preenchimento, suporte, aderência; defeitos de impressão e correções (com fontes) |
| `logo-em-relevo` | Transformar imagem/logo/texto em relevo ou gravação |

Para criar uma skill nova, siga [.claude/skills/README.md](.claude/skills/README.md).
Quando descobrir uma técnica que funcionou (ou um erro que custou tempo), registre na skill
correspondente ou nesta seção de armadilhas.

## Limites

- O Claude não envia nada para a impressora. Quem imprime é o usuário, pelo Bambu Studio.
- Não instale pacotes no sistema nem add-ons no Blender sem pedir.
- Não apague arquivos de `referencias/` nem projetos inteiros sem confirmação.
