---
name: fluxo-projeto
description: Mapa do fluxo de trabalho de um projeto 3D neste repositório, da referência à peça impressa — fases, portões de aprovação, quando perguntar ao usuário, quais ferramentas abrir (Blender headless, Blender com interface, ponte ao vivo, Bambu Studio), como abrir e como usar cada uma. Use ao iniciar qualquer projeto, ao retomar um projeto existente ("continua a caneca"), ou quando não estiver claro qual é o próximo passo.
---

# Fluxo de um projeto 3D

```
F0 Entrada → F1 Sabatina ⛔ → F2 Modelagem por etapas ⛔⛔⛔ → F3 Peça de teste ⛔ → F4 Fatiar e entregar ⛔ → F5 Pós-impressão
```

⛔ = portão: só avance com "sim" explícito do usuário. Use `AskUserQuestion` com opções
curtas (ex.: "Aprovar e seguir (Recomendado)", "Ajustar", "Voltar para a sabatina").

## Retomar um projeto

Leia primeiro `projetos/<nome>/README.md`: o campo **Status** diz a fase atual e a seção
**Especificação** diz o que foi combinado. Não repita perguntas já respondidas. Continue
da fase registrada.

Status possíveis: `entrada` → `sabatina` → `especificado` → `modelando: base|recursos|acabamento`
→ `teste` → `pronto para imprimir` → `impresso` → `finalizado`.

## F0. Entrada

Gatilho: o usuário traz fotos, medidas, link ou descrição de algo novo.

1. Crie a pasta: `tools/novo_projeto.sh <nome-em-kebab-case> "Descrição curta"`.
   Nome: sugira um e siga; o usuário corrige se quiser.
2. Copie as referências para `projetos/<nome>/referencias/` com nomes descritivos
   (copiar, não mover, salvo pedido do usuário).
3. Status: `sabatina`. Vá para F1.

Não pergunte nada ainda além do nome, se for ambíguo.

**Entrada pela Oficina 3D (interface).** A pasta e `referencias/` já vêm prontas; o pedido traz
a descrição, o que a pessoa quer, o modelo gerado por IA (`.3mf`, `.stl` ou `.obj`) e as
imagens. Comece inspecionando o modelo da IA
(`tools/blender.sh tools/inspecionar.py -- <modelo> --saida projetos/<nome>/saida/inspecao_modelo_ia`):
tamanho real, malha fechada, ilhas soltas, espessura. Modelo de IA costuma vir na escala
errada, sem base plana e com partes finas demais: leve isso para a sabatina como perguntas.

## F1. Sabatina ⛔

Carregue a skill `grill-me` e siga-a até o fim. Saída: seção **Especificação** completa no
README (requisitos com fonte, critérios de aceite, estratégia de modelagem, fora de escopo,
riscos) e aprovação explícita.

Portão G1: "Especificação aprovada?" Com aprovação: Status `especificado`.

## F2. Modelagem por etapas ⛔⛔⛔

Construa em 3 etapas, mostrando cada uma. Erro de forma descoberto na etapa 1 custa uma
regeneração; descoberto no fim custa refazer tudo.

| Etapa | Conteúdo | O usuário confere |
| --- | --- | --- |
| 2a Base | Volume principal, medidas externas, paredes, base plana, orientação de impressão | Tamanho, proporção, orientação |
| 2b Recursos | Furos, encaixes, abas, alças, texto/logo, divisões | Posição e tamanho de cada recurso |
| 2c Acabamento | Chanfros, arredondados, texturas, limpeza | Aparência final |

Peça simples (ex.: placa com dois furos): a especificação pode juntar 2a+2b+2c numa etapa.

Em cada etapa:
1. Edite `projetos/<nome>/modelo.py` (skill `modelagem-blender`). Status `modelando: <etapa>`.
2. Gere: `tools/blender.sh projetos/<nome>/modelo.py 2>&1 | grep -vE "render +\| Saved|^$" | tail -40`
3. Autorrevisão (abaixo). Corrija o que falhar ANTES de mostrar ao usuário.
4. Mostre ao usuário (ver "Como mostrar o modelo"). Liste em 3–5 linhas o que foi feito,
   medidas principais e dúvidas.
5. Portão: "Etapa aprovada?" Ajustes pedidos: aplique e mostre de novo.
   Pedido que muda requisito: volte à `grill-me` só nesse galho, atualize a especificação.

### Autorrevisão (antes de cada portão)

Leia `saida/preview/folha.png` e `saida/relatorio.json` e confira:

- [ ] Forma bate com as referências e com a especificação.
- [ ] Todos os recursos desta etapa estão presentes e no lugar certo.
- [ ] `dimensoes_mm` bate com a especificação (tolerância de 0.1 mm nas críticas).
- [ ] `malha_fechada: true`, sem avisos não explicados.
- [ ] Nenhuma parte solta ou flutuando; base plana em Z=0.
- [ ] Overhangs dentro do limite ou previstos na especificação (suporte aceito).
- [ ] Paredes ≥ 1.2 mm, detalhes ≥ 0.8 mm, texto ≥ 4 mm.
- [ ] Chanfros/arredondados nas arestas certas (chanfro embaixo).
- [ ] Critérios de aceite da especificação atendidos até aqui.

## F3. Peça de teste ⛔ (quando houver encaixe ou medida crítica)

Antes de gastar a peça inteira, gere um recorte pequeno só da região crítica
(encaixe, furo, rosca, interface com objeto real): `malha.booleana(peca, caixa, "INTERSECT")`
num script `projetos/<nome>/teste_encaixe.py`, exporte e fatie (F4) com o MESMO processo,
filamento e ajustes da peça final (a folga real muda com eles). Informe tempo e gramas.

Portão G3: o usuário imprime e relata. Ajuste os parâmetros de folga, registre no
Histórico e repita até encaixar. Sem medida crítica: pule F3 (registre "não se aplica").

## F4. Fatiar e entregar ⛔

Skills `preparar-impressao` (checagem, fatiamento, entrega) e `configuracao-impressao`
(costura, camadas, paredes, preenchimento, suporte, aderência). Resumo:
1. `python3 tools/fatiar.py projetos/<nome>/saida/<peça>.stl --processo ... --ajuste CHAVE=VALOR ...`
2. Informe tempo, gramas, processo, filamento, orientação, avisos.
3. Abra no Bambu Studio para o usuário: `bambu-studio "<3mf>" >/dev/null 2>&1 &`
4. Status `pronto para imprimir`. Atualize a tabela Impressão do README.

Portão G4: o usuário confirma que vai imprimir (ou pede mudanças).

## F5. Pós-impressão

Quando o usuário relatar o resultado:
1. Registre no Histórico: data, versão (parâmetros), resultado, fotos se houver.
2. Problema de impressão (warping, fio, suporte): ajuste processo/orientação.
   Problema de projeto (medida, encaixe): ajuste parâmetro; se mudar requisito, `grill-me`.
3. Aprovado: Status `finalizado`. Guarde lições que valem para outros projetos na skill
   correspondente ou em "API do Blender 5.x — armadilhas" do `CLAUDE.md`.

## Ferramentas: quando e como abrir

| Ferramenta | Quando | Como |
| --- | --- | --- |
| Blender headless | Sempre para gerar, exportar, checar, renderizar | `tools/blender.sh <script.py> [-- args]` |
| Visualizar previews | Em toda autorrevisão (você) e em todo portão (usuário) | Você: Read em `saida/preview/folha.png`. Usuário: link clicável para o PNG na resposta |
| Blender com interface | Usuário quer girar/inspecionar em 3D, ou editar à mão | `blender "projetos/<nome>/saida/modelo.blend" >/dev/null 2>&1 &` |
| Ponte ao vivo | Blender já aberto e o usuário quer acompanhar ou falar da seleção | Skill `blender-ao-vivo` (`python3 tools/blender_ponte/cliente.py --status`) |
| Inspecionar STL externo | Usuário traz STL baixado ou de outro programa | `tools/blender.sh tools/inspecionar.py -- arquivo.stl` |
| Vetorizar logo | Logo/arte em imagem | `python3 tools/imagem_para_svg.py` (skill `logo-em-relevo`) |
| Bambu Studio CLI | F3 e F4: tempo, peso, 3MF | `python3 tools/fatiar.py ...` |
| Bambu Studio interface | Entrega (F4), conferir suporte/multicor, enviar à impressora | `bambu-studio "<caminho absoluto do 3mf>" >/dev/null 2>&1 &` (relativo abre vazio) |
| Pesquisa web | Medidas de produtos e peças comerciais (F1) | WebSearch/WebFetch; duas fontes para medida crítica |

Abrir janelas (Blender, Bambu Studio) é para o usuário. Não abra se ele não for olhar.
O `&` e o redirecionamento evitam travar o terminal e poluir a saída.

### Como mostrar o modelo ao usuário

- Padrão: link para `projetos/<nome>/saida/preview/folha.png` + resumo em texto.
- Detalhe específico: link para a vista individual (`iso.png`, `frente.png`, `lado.png`, `topo.png`).
- Quer girar: abra o `.blend` no Blender (tabela acima) ou rode pela ponte, se aberto.

## Economia de tokens

- A sabatina completa antes de modelar é a maior economia: evita refazer etapas.
- Junte vários ajustes pequenos numa única regeneração.
- Por iteração, leia só `folha.png` (uma imagem). Vistas individuais só para detalhe.
- Filtre a saída do Blender (`grep -vE ...`, `tail`). Procure `RELATORIO_JSON`.
- Edite parâmetros com Edit em vez de reescrever `modelo.py` inteiro.
- Não fatie a cada iteração: fatie em F3 e F4.
- Não releia o README inteiro a cada passo; ele é para retomar sessões.
