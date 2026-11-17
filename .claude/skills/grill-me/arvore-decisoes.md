# Árvore de decisões de um projeto 3D

Galhos na ordem em que normalmente se resolvem. Cada galho lista as perguntas típicas
e a recomendação padrão. Adapte ao objeto: pule o que não se aplica (marcando
"não se aplica" com o motivo) e aprofunde o que for crítico.

## 1. Objetivo e uso

- O que é a peça e qual problema resolve?
- Decorativa, funcional ou protótipo para testar forma?
- Onde fica (mesa, parede, carro, cozinha, ao ar livre) e quem usa?
- Quantas unidades? Uma de cada vez ou várias por placa?
- Existe peça original (quebrada, de outro fabricante) que estamos copiando ou melhorando?

Recomendação padrão: protótipo funcional primeiro, uma unidade, ajuste antes de produzir.

## 2. Referências e medição

- Qual referência manda quando duas discordarem (foto vs. medida anotada vs. desenho)?
- As fotos têm escala? Se não: o usuário consegue medir o objeto real?
- Ferramenta de medição disponível: paquímetro (±0.05 mm), régua (±0.5 mm), trena?
- Peças comerciais envolvidas: modelo exato (para pesquisar dimensões oficiais).

Como pedir fotos úteis (envie ao usuário quando as fotos não bastarem):
- Uma foto por face principal (frente, lado, topo), câmera perpendicular à face, longe e
  com zoom para reduzir perspectiva.
- Régua ou paquímetro encostado na face fotografada, no mesmo plano da medida.
- Fundo liso e contrastante, boa luz, sem flash estourando.
- Detalhes críticos (furos, encaixes, abas) em close, também com escala.

## 3. Dimensões

- Envelope máximo (largura x profundidade x altura) e de onde vem cada limite.
- Medidas críticas (encaixe, furo, vão): valor, como foi medido, tolerância.
- Medidas livres: faixa aceitável ("entre 80 e 100 mm").
- Espessuras mínimas impostas por uso (parede que leva carga, base que leva parafuso).

Recomendação padrão: folga de 0.2 mm por lado em encaixe justo, 0.4 mm em encaixe solto;
para furo de parafuso, diâmetro nominal + 0.3–0.4 mm.

## 4. Interfaces e fixação

- Com o que a peça se conecta? Parafuso (tipo, bitola, cabeça, comprimento), porca,
  inserto de latão por calor, ímã (diâmetro x altura), encaixe por pressão (snap-fit),
  dobradiça, rosca impressa, cola, fita dupla face.
- Precisa desmontar? Quantas vezes?
- Alinhamento entre peças (pinos, rebaixos).

Recomendação padrão: parafuso M3 com inserto de latão (furo 4.2 mm, parede ≥ 1.6 mm) para
uniões que desmontam; ímã 6x3 mm com folga de 0.15 mm no diâmetro para fixação leve;
snap-fit só em PETG, com haste fora do eixo Z.

## 5. Esforço e ambiente

- Carga: peso suportado, impacto, flexão, torção. Direção da força.
- Temperatura: sol, carro, perto de motor, líquido quente, lava-louças.
- Umidade, água, UV, produtos químicos.
- Contato com alimento ou pele.

Avisos obrigatórios:
- Alimento/bebida: FDM não é seguro para contato direto (linhas de camada acumulam
  bactérias). Alternativas: uso decorativo, resina food-safe, inserto de vidro/aço.
- Calor: PLA amolece a ~55–60 °C. Carro ao sol, líquido quente: PETG ou ASA.

Recomendação padrão: uso interno, sem calor, carga leve, PLA.

## 6. Material, cor e acabamento

- Quais filamentos e cores o usuário tem disponíveis? (Não recomende o que ele não tem
  sem avisar que precisa comprar.)
- Tem AMS lite (multicor automático)? Se não, aceita troca manual por altura?
- Acabamento: fosco, seda, liso; aceita lixar, pintar, aplicar resina?
- Face mais importante visualmente (define orientação: a face na mesa fica com a textura
  da placa PEI).

Recomendação padrão: Bambu PLA Basic, uma cor, sem pós-processamento.

## 7. Estética e detalhes

- Estilo: reto/técnico, arredondado/orgânico, igual à referência?
- Bordas: chanfro (melhor para impressão) ou arredondado?
- Texto ou logo: conteúdo exato, fonte, tamanho, relevo ou gravado, arquivo original
  (SVG/PNG de alta resolução) existe?
- Texturas (martelado, ranhuras, padrão).

Recomendação padrão: chanfro de 0.6–1 mm nas arestas de baixo, arredondado nas de cima.

## 8. Fabricação

- Cabe na A1 mini (180 x 180 x 180 mm, margem de 5 mm)? Se não: dividir onde e como unir?
- Orientação preferida e se suporte é aceitável (onde as marcas de suporte podem ficar).
- Prioridade: qualidade, resistência ou velocidade? Define camada (0.12/0.16/0.20/0.28).
- Limite de tempo de impressão ou de gramas de filamento?
- Peça de teste antes (só o encaixe crítico, poucos gramas)?
- Qual face pode receber a costura (seam)? Em peça redonda (caneca, vaso) a costura
  sempre aparece em algum lugar: atrás da alça, numa aresta, ou espalhada (random)?
- Direção do esforço principal: define orientação (camadas nunca devem ser puxadas
  para se separar) e número de paredes.
- Acabamento do topo: precisa ficar liso (ironing) ou linhas de camada são aceitáveis?
- Detalhes finos (texto, logo, pinos) abaixo de 0.8 mm: aceitar perda, engrossar ou
  usar camada/linha mais fina?

Recomendação padrão: sem suporte, camada 0.20 mm, costura alinhada numa aresta ou atrás,
peça de teste quando houver encaixe crítico. Detalhes de configuração do fatiador: skill
`configuracao-impressao`.

## 9. Montagem

- Uma peça ou conjunto? Ordem de montagem?
- Peças compradas (parafusos, ímãs, insertos): o usuário já tem? Quais medidas exatas?

## 10. Entrega e aceite

- O que é "pronto": STL? 3MF fatiado? Peça impressa e testada?
- Como validar: encaixa em X, aguenta Y, fica bonita em Z.
- Prazo ou urgência?
- Quantas rodadas de ajuste o usuário espera (para planejar peça de teste)?

Recomendação padrão: 3MF fatiado aberto no Bambu Studio + checklist de aceite no README.
