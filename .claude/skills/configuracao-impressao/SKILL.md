---
name: configuracao-impressao
description: Escolhe e aplica as configurações do fatiador Bambu Studio para cada peça na A1 mini — posição e tipo de costura (seam: aligned/back/nearest/random/scarf), altura de camada, número de paredes, camadas de topo e fundo, padrão e densidade de preenchimento, gerador de paredes (classic/arachne), suporte, brim, pé de elefante, ironing, vaso espiral — com base na Wiki da Bambu Lab, Prusa e testes da comunidade. Também diz o que checar na malha antes de fatiar. Use sempre antes de fatiar uma peça final ou de teste, quando o usuário perguntar sobre configurações de impressão, ou quando uma impressão saiu com defeito (fios, empeno, costura aparente, topo furado, camadas separando).
---

# Configuração de impressão

Arquivos desta skill:
- [parametros-bambu.md](parametros-bambu.md): toda chave do Bambu Studio que usamos, valores
  válidos, padrão da A1M, rótulo pt-BR da interface e quando mudar.
- [conhecimento.md](conhecimento.md): o porquê (resistência, costura, tolerâncias, defeitos e
  correções), com fontes.

Aplicação: `python3 tools/fatiar.py <stl> --processo "<preset>" --ajuste CHAVE=VALOR ...`.
O `fatiar.py` confere cada ajuste no G-code. Ajuste com `ok: false` = chave ou valor
inválido (o Bambu ignora em silêncio): corrija antes de entregar.

## 1. Barreira de malha (antes de qualquer configuração)

No Linux o Bambu Studio NÃO tem o reparo Netfabb ("Corrigir modelo" é só Windows); a
checagem do Blender é a única barreira. Rode o modelo (ou `tools/inspecionar.py`) e
exija no `relatorio.json`:

| Campo | Exigência |
| --- | --- |
| `malha_fechada`, `bordas_abertas`, `arestas_com_3_ou_mais_faces` | fechada, 0, 0 |
| `autointersecoes` | 0 |
| `ilhas_flutuando` | 0 |
| `faces_degeneradas` | 0 (ou `malha.limpar`) |
| `area_abaixo_detalhe_min_pct` | ≤ 0.5 ou aceito pelo usuário (detalhe vai sumir) |
| `area_abaixo_parede_min_pct` | ≤ 5 ou aceito pelo usuário |

Falhou: volte ao modelo. Não "conserte no fatiador".

## 2. Classificar a peça e partir de um perfil

| Perfil | Preset base | Ajustes |
| --- | --- | --- |
| **Funcional** (suporte, gancho, encaixe, caixa) | `0.20mm Standard @BBL A1M` | `wall_loops=4` `sparse_infill_density=20%` `sparse_infill_pattern=gyroid` `bottom_shell_layers=4` `precise_outer_wall=1` |
| **Carga alta** (prateleira, ferramenta, peça que leva parafuso apertado) | `0.20mm Strength @BBL A1M` (6 paredes, 25%) | `sparse_infill_pattern=cubic` se esforço em várias direções |
| **Decorativa lisa** (vaso, figura, caneca decorativa) | `0.16mm Optimal @BBL A1M` | `wall_loops=3` `sparse_infill_density=10%` `sparse_infill_pattern=adaptivecubic` + regra de costura (seção 3) |
| **Detalhe fino** (texto pequeno, logo, miniatura) | `0.12mm Fine @BBL A1M` | `wall_generator=arachne` |
| **Placa plana com topo à vista** (plaquinha, tampa, chaveiro) | `0.16mm Optimal @BBL A1M` | `ironing_type=top` `top_surface_pattern=monotonic` `top_shell_layers=6` |
| **Vaso de parede única** | `0.20mm Standard @BBL A1M` | `spiral_mode=1` `bottom_shell_layers=5` (modelo sem topo, sem recurso interno) |
| **Peça de teste de encaixe** | o MESMO processo e filamento da peça final | nenhum: tolerância muda com processo/filamento |
| **Rascunho de forma** | `0.28mm Extra Draft @BBL A1M` | `sparse_infill_density=10%` |

Perfis são ponto de partida. Ajuste pelas seções abaixo e pela especificação.

## 3. Costura (decida sempre, nunca deixe no automático)

Testado nesta A1 mini (cilindro Ø30, 2026-10-17): `back` pôs a costura em +Y (fundo da
mesa) em todas as camadas; `aligned` pôs em -Y (frente); `nearest` e `random` espalharam
pela volta inteira.

| Forma | Configuração |
| --- | --- |
| Peça com cantos (caixa, suporte) | `seam_position=aligned`: a costura cai numa aresta e some |
| Peça redonda com face nobre (caneca com logo, vaso com relevo) | `seam_position=back` + `seam_slope_type=external`; modele a face nobre em -Y (frente, padrão de `logo.enrolar_em_cilindro`) e a alça/lado escondido em +Y |
| Peça redonda sem face nobre | `seam_position=back` + `seam_slope_type=external` |
| Textura que já esconde tudo (fuzzy skin, martelado forte) | `aligned` ou `back`; `random` só se o usuário aceitar "pontinhos" |

Nunca use `nearest` em peça redonda ou orgânica: sem cantos, a costura segue o
deslocamento do bico e se espalha. `random` é a causa mais comum de "pontinhos" na parede
segundo a Bambu. Se o usuário quiser um lugar exato: pintura de costura na interface do
Bambu Studio (avise que é passo manual dele).

## 4. Camadas, paredes, cascas e preenchimento

- **Altura de camada**: escolha pelo preset (não só `layer_height`), que ajusta cascas,
  suporte e velocidades juntos. Superfície curva à vista ou detalhe < 1 mm: 0.12–0.16.
  Funcional: 0.20. Limite do bico 0.4: 0.08–0.28.
- **Resistência**: suba `wall_loops` antes de `sparse_infill_density`. Acima de ~30% de
  preenchimento o ganho é pequeno para o tempo/material.
- **Camadas sempre são o ponto fraco**: oriente para a carga ficar no plano XY.
- **Topo**: `top_shell_layers` ≥ 5 em 0.20 (≥ 1 mm). Preenchimento ≤ 10% ou lightning:
  suba para 6–7 para não "almofadar" o topo.
- **Fundo que veda** (copo, vaso, caixa estanque): `bottom_shell_layers=4–5`, paredes ≥ 3.
- **Padrão**: grid é o padrão do preset, mas raspa o bico e empena peça grande; prefira
  `gyroid` (geral/peça grande), `cubic` (carga em todas as direções), `adaptivecubic`
  (economia em peça grande), `lightning` só decorativo.
- **Detalhe fino**: `wall_generator=arachne`. Superfície ruim ou parede solta com arachne:
  volte a `classic`.

## 5. Aderência, precisão e suporte

- Brim: peça com base pequena e alta, ou cantos agudos grandes: `brim_type=outer_only`
  `brim_width=5–8`. Base larga e plana: `no_brim`.
- Encaixe crítico na base: `elefant_foot_compensation=0.15–0.2` (preset A1M vem 0) ou
  chanfro de 0.4–0.6 mm na aresta de baixo do modelo (preferível).
- Encaixe crítico em geral: `precise_outer_wall=1`; folga no modelo, não `xy_hole_compensation`.
- Suporte: só se o modelo não resolver (chanfro 45°, furo em gota, reorientar).
  Overhang plano grande: `support_type=normal(auto)`; pequeno/orgânico: `tree(auto)`.
  Sem marcas sobre a peça: `support_on_build_plate_only=1`.
- Peça alta e fina (a mesa da A1 mini se move em Y): brim, e avise o usuário. Ver
  conhecimento.md, seção "Mesa móvel".

## 6. Aplicar, conferir, registrar

1. Fatie com preset + ajustes.
2. Confira no JSON: `ok: true`, todos os `ajustes.*.ok: true`, `erros_cli` vazio.
3. Erro "empty layer" ou "Nothing to be sliced": malha com defeito ou peça fora da mesa.
4. Informe ao usuário em 3–4 linhas: preset, ajustes principais e o porquê, tempo, gramas.
5. Registre no README do projeto (tabela Impressão): preset + linha de `--ajuste`
   completa, para repetir a impressão igual.
6. Resultado da impressão (F5 do fluxo): defeito → tabela de defeitos em conhecimento.md.
