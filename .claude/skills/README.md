# Skills deste repositório

Cada skill é uma pasta com um `SKILL.md`. O Claude Code carrega as skills de
`.claude/skills/` automaticamente; o usuário também pode chamar com `/<nome>`.

## Formato

```
.claude/skills/<nome-da-skill>/
  SKILL.md            obrigatório
  referencia.md       opcional: material longo, lido só quando necessário
  scripts/            opcional: scripts que a skill manda rodar
```

`SKILL.md` começa com frontmatter YAML:

```markdown
---
name: nome-da-skill
description: O que a skill faz e QUANDO usar. Inclua as palavras que o usuário diria
  ("caneca", "encaixe", "logo", "fatiar"). É o que o Claude lê para decidir se carrega.
---

# Título

Instruções diretas, no imperativo. Passos numerados para fluxos.
Comandos exatos em blocos de código.
```

## Boas práticas

- Uma skill = um tipo de tarefa. Se crescer demais, divida ou mova detalhes para `referencia.md`.
- Escreva o que não é óbvio: decisões, armadilhas, valores que funcionaram na A1 mini.
- Use os utilitários de `tools/` em vez de repetir código dentro da skill.
- Atualize a tabela de skills no `CLAUDE.md` ao criar uma nova.

## Skills existentes

| Skill | Uso |
| --- | --- |
| `fluxo-projeto` | Fases, portões de aprovação e ferramentas de um projeto |
| `grill-me` | Sabatina de requisitos antes de modelar (+ `arvore-decisoes.md`) |
| `modelagem-blender` | Receitas bpy para o `modelo.py` |
| `blender-ao-vivo` | Ponte com o Blender aberto |
| `preparar-impressao` | Checagem, orientação, fatiamento, Bambu Studio |
| `configuracao-impressao` | Configurações do fatiador e base de conhecimento (+ `parametros-bambu.md`, `conhecimento.md`) |
| `logo-em-relevo` | Imagem/logo/texto para relevo ou gravação |

Ideias para próximas skills: `encaixes-e-tolerancias` (snap-fit, rosca, dobradiça),
`multicor-ams` (pintura por objeto/altura), `engenharia-reversa` (modelar a partir de fotos e medidas).
