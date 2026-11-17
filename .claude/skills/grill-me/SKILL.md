---
name: grill-me
description: Sabatina o usuário antes de modelar qualquer peça 3D. Percorre a árvore de decisões do projeto (função, medidas, encaixes, ambiente, material, estética, fabricação, aceite), pergunta tudo o que não se sabe, com uma resposta recomendada em cada pergunta, e só libera a próxima etapa quando a especificação está completa e aprovada. Use SEMPRE no início de um projeto novo, quando o usuário trouxer fotos/medidas/referências, quando disser "grill me", "me sabatine", "me entrevista", ou quando surgir informação nova que mude requisitos de um projeto em andamento.
---

# Grill-me: sabatina de projeto 3D

Objetivo: zero suposição silenciosa. Retrabalho de modelagem e de impressão custa muito
mais tokens, filamento e tempo do que algumas perguntas a mais no início.

## Regras

1. **Nada de modelar antes da aprovação.** Enquanto a sabatina estiver aberta, não escreva
   `modelo.py`, não rode Blender, não fatie. A única exceção é ler referências e pesquisar.
2. **Investigue antes de perguntar.** Se a resposta está nas referências (fotos, desenhos,
   arquivos), no repositório (`config/impressora.json`, projetos anteriores) ou é um dado
   público (dimensões de produto comercial, parafuso, ímã, conector), descubra você mesmo.
   Pesquise na web, cruze duas fontes quando a medida for crítica e cite a fonte na
   especificação. Mesmo assim, apresente o valor encontrado para o usuário confirmar.
3. **Toda pergunta traz sua recomendação.** Formato: pergunta objetiva + opção recomendada
   com o motivo em uma linha. O usuário deve poder responder "ok" ou clicar.
4. **Siga a árvore, respeitando dependências.** A cada rodada, pergunte só o que não depende
   de respostas pendentes. Exemplo: não pergunte o diâmetro do ímã antes de saber se a
   fixação será por ímã.
5. **Lotes pequenos.** No máximo 4 perguntas independentes por rodada, das de maior impacto
   para as de menor. Use a ferramenta `AskUserQuestion` quando as respostas forem opções
   discretas (recomendada primeiro, com "(Recomendado)" no rótulo). Medidas e textos livres:
   pergunte em texto, numa lista numerada, para o usuário responder em uma mensagem.
6. **Não aceite resposta vaga em item crítico.** "Mais ou menos 10 cm" para uma medida de
   encaixe não serve: peça a medida com paquímetro/régua ou proponha imprimir uma peça de
   teste. Para itens não críticos, registre a tolerância aceita.
7. **Registre a cada rodada.** Atualize a seção "Especificação" do `README.md` do projeto
   depois de cada resposta. Se a sessão cair, a próxima retoma de onde parou.
8. **Diga o que vai assumir.** Padrões (impressora, bico, PLA, placa) entram na
   especificação marcados como "padrão". O usuário vê e confirma na aprovação final.
9. **Conflito ou dúvida nova reabre o galho.** Se durante a modelagem aparecer algo que a
   especificação não cobre ou que contradiz o combinado, pare, volte a esta skill só para
   aquele galho, atualize a especificação e peça aprovação da mudança.

## Procedimento

### 1. Ler tudo que o usuário trouxe

- Abra cada imagem com Read. Descreva em 3–6 linhas o que você entendeu: objeto, forma,
  detalhes, o que parece ser medida crítica, o que está ambíguo.
- Identifique se há referência de escala nas fotos (régua, cartão, moeda, medida anotada).
  Sem escala, nenhuma dimensão pode vir da foto: precisa de medida do usuário.
- Pesquise dados públicos do que for comercial (modelo do celular, controle, parafuso...).

### 2. Montar a árvore de decisões

Use os galhos de [arvore-decisoes.md](arvore-decisoes.md). Para cada galho, marque:
`resolvido` (com valor e fonte), `não se aplica` (com motivo), `pendente`.
Galhos irrelevantes para o objeto são marcados `não se aplica` sem perguntar,
mas aparecem na especificação para o usuário poder discordar.

### 3. Rodadas de perguntas

Repita até não haver `pendente`:
1. Escolha até 4 perguntas pendentes sem dependência entre si, por impacto.
2. Pergunte (regras 3, 5 e 6).
3. Registre as respostas na especificação.
4. Avalie se as respostas abriram galhos novos (ex.: "vai na parede" abre fixação).

Se o usuário disser "pode assumir o resto": preencha os pendentes com os padrões
recomendados, marque cada um como "assumido", e siga para a aprovação. Itens críticos
(medidas de encaixe, segurança alimentar/calor) nunca são assumidos: pergunte mesmo assim.

### 4. Especificação para aprovação

Preencha no `README.md` do projeto (modelo em `projetos/_modelo/README.md`):

- **Resumo** em 2–3 linhas.
- **Requisitos**: tabela `Item | Valor | Fonte` (usuário, referência, pesquisa com link,
  padrão, assumido).
- **Critérios de aceite**: como saberemos que a peça está certa (encaixa em X, aguenta Y,
  cabe em Z, aparência W).
- **Estratégia de modelagem**: técnica principal, número de peças, orientação de impressão,
  etapas de modelagem, parâmetros que ficarão ajustáveis.
- **Fora de escopo**: o que não será feito agora.
- **Riscos**: o que pode dar errado e como mitigar (ex.: peça de teste de encaixe).

Mostre ao usuário um resumo curto (não o README inteiro) e pergunte com `AskUserQuestion`:
"Especificação aprovada?" com opções: aprovar / ajustar itens. Só com aprovação explícita:
marque `Status da especificação: aprovada em AAAA-MM-DD` e siga para a próxima fase
do fluxo (skill `fluxo-projeto`, Fase 3).

## Anti-padrões

- Despejar 20 perguntas de uma vez.
- Perguntar o que estava na foto, no config ou é dado público.
- Perguntar sem recomendar.
- "Vou começar com um rascunho enquanto você responde." Não vai.
- Tratar medida estimada de foto sem escala como medida real.
- Aprovação implícita ("o usuário não reclamou"). Precisa de "sim".
