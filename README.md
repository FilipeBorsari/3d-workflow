# Projetos 3D

Modelagem 3D para impressão na Bambu Lab A1 mini, feita com o Claude Code.
O Claude escreve scripts Python para o Blender, confere o modelo por imagens e relatório,
e fatia no Bambu Studio. Você revisa e imprime.

Instruções completas para o Claude: [CLAUDE.md](CLAUDE.md).

## Oficina 3D (interface visual)

Para quem não usa VS Code nem terminal. Roda no próprio computador e abre no navegador.

1. Instale o [Node.js](https://nodejs.org) 20 ou mais novo.
2. Inicie: no Linux, `./iniciar.sh`; no Windows, clique duas vezes em `iniciar.bat`.
   Na primeira vez ele instala as dependências (precisa de internet).
3. O navegador abre em http://localhost:3333 com o passo a passo:
   programas necessários (Blender, Bambu Studio, Python, Git no Windows), login com a conta
   Claude, e criação de projeto a partir do `.3mf` gerado por uma IA + imagens de referência.

A Oficina usa o Claude Code que vem junto com o Agent SDK (não precisa instalar o Claude Code)
e conversa com o Claude dentro do projeto. Perguntas e aprovações do fluxo aparecem como
botões. O Claude roda os comandos do repositório sem pedir permissão a cada um: use em
máquina de confiança. A conversa de cada projeto fica em `projetos/<nome>/.app/`.
Código em [app/](app/).

## Requisitos

- Blender 5.x no PATH (`blender`)
- Bambu Studio no PATH (`bambu-studio`), já aberto pelo menos uma vez (para baixar os presets)
- Python 3 com Pillow e numpy
- Opcional: `potrace` (`sudo apt install potrace`) para vetorizar logos com mais qualidade

## Como usar

Converse com o Claude neste diretório. Todo projeto novo começa com uma sabatina
(skill `grill-me`): o Claude pergunta tudo que não souber, com uma recomendação em cada
pergunta, e só começa a modelar depois que você aprovar a especificação. Depois, cada
etapa da modelagem (base, recursos, acabamento) é mostrada para aprovação.
Para forçar a sabatina a qualquer momento: `/grill-me`. Para ver o fluxo: `/fluxo-projeto`.

Exemplos:

- "Quero um suporte de parede para meu controle, a foto está em ~/Downloads/controle.jpg"
- "Ajusta a caneca: 5 mm mais alta e logo maior"
- "Fatia a caneca em 0.16 e me diz tempo e peso"
- "Estou com o Blender aberto, olha o objeto selecionado e arredonda as quinas"

## Comandos úteis

```bash
tools/novo_projeto.sh meu-projeto "Descrição"                 # cria projetos/meu-projeto
tools/blender.sh projetos/meu-projeto/modelo.py               # gera STL, .blend, relatório e previews
tools/blender.sh tools/inspecionar.py -- arquivo.stl          # inspeciona qualquer STL
python3 tools/fatiar.py projetos/meu-projeto/saida/peca.stl   # fatia no Bambu Studio (CLI)
python3 tools/imagem_para_svg.py logo.png -o logo.svg         # vetoriza logo
```

## Blender ao vivo (opcional)

Para o Claude ver e mexer no Blender que você está usando:

```bash
tools/blender_ponte/instalar.sh     # uma vez; depois reinicie o Blender
```

A ponte aparece no Blender em Viewport 3D > N > aba Claude, e escuta só em
`127.0.0.1:9876`. Para remover: `tools/blender_ponte/instalar.sh --remover`.

## Estrutura

```
config/impressora.json   impressora, presets e regras de projeto
.claude/skills/          skills do Claude (fluxo-projeto, grill-me, modelagem-blender,
                         blender-ao-vivo, preparar-impressao, configuracao-impressao,
                         logo-em-relevo)
tools/                   scripts e biblioteca bpy (tools/bl)
projetos/<nome>/         README, modelo.py, referencias/, saida/
```
