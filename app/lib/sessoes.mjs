// Uma conversa com o Claude por projeto, pelo Claude Agent SDK. Cada mensagem da pessoa é um
// query() que retoma a sessão anterior (resume). Os eventos vão para a interface por SSE e ficam
// gravados em projetos/<nome>/.app/conversa.jsonl para a conversa reaparecer ao reabrir.
//
// Perguntas e portões de aprovação: o fluxo do repositório usa a ferramenta AskUserQuestion.
// O canUseTool segura a chamada, mostra a pergunta como botões e devolve as respostas.
import { query } from "@anthropic-ai/claude-agent-sdk";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { executavelClaude } from "./login.mjs";

const IMAGEM = /\.(png|jpe?g|webp|gif)$/i;

// Ferramentas que não fazem sentido para quem usa a interface.
const BLOQUEADAS = [
  "Artifact",
  "Workflow",
  "CronCreate",
  "CronDelete",
  "RemoteTrigger",
  "ScheduleWakeup",
  "PushNotification",
  "EnterWorktree",
  "ShareOnboardingGuide",
];

function instrucoes(nome) {
  return `
# Interface Oficina 3D

Você está rodando dentro da Oficina 3D, uma interface web local para este repositório.
A pessoa do outro lado NÃO vê terminal nem VS Code e pode não ser técnica.

- Projeto atual: projetos/${nome}. Trabalhe só nele, salvo pedido explícito.
- Toda pergunta à pessoa e todo portão ⛔ do fluxo: use AskUserQuestion. A interface mostra as
  opções como botões. Não faça perguntas soltas no texto esperando resposta.
- Escreva em português simples, frases curtas, sem jargão de programação. Não mostre código,
  comandos nem caminhos longos, salvo se a pessoa pedir. Explique medidas em mm.
- Para mostrar um resultado, leia (Read) as imagens em projetos/${nome}/saida/preview/ ou outra
  imagem dentro do projeto: a interface exibe para a pessoa toda imagem que você lê dentro da
  pasta do projeto. Leia a imagem antes de perguntar se a pessoa aprova a etapa.
- A interface tem botões "Abrir no Bambu Studio" para cada .3mf em saida/ e saida/fatiado/, e
  "Abrir no Blender" para saida/modelo.blend. Diga qual arquivo abrir; não precisa abrir por comando.
- A pessoa não imprime pela interface: a entrega é o .3mf pronto, que ela abre no Bambu Studio.
`;
}

export function criarSessoes({ RAIZ, projetos, ambiente }) {
  const sessoes = new Map();

  function pastaApp(nome) {
    const p = path.join(projetos.pastaProjeto(nome), ".app");
    mkdirSync(p, { recursive: true });
    return p;
  }

  function sessao(nome) {
    if (!sessoes.has(nome)) {
      let sessionId = null;
      try {
        sessionId = JSON.parse(readFileSync(path.join(pastaApp(nome), "sessao.json"), "utf8")).sessionId;
      } catch {}
      sessoes.set(nome, { nome, sessionId, rodando: false, consulta: null, pergunta: null, clientes: new Set(), passo: null });
    }
    return sessoes.get(nome);
  }

  function historico(nome) {
    const arq = path.join(pastaApp(nome), "conversa.jsonl");
    if (!existsSync(arq)) return [];
    return readFileSync(arq, "utf8")
      .split("\n")
      .filter(Boolean)
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  }

  function estado(nome) {
    const s = sessao(nome);
    return { rodando: s.rodando, pergunta: s.pergunta ? s.pergunta.evento : null, passo: s.passo };
  }

  function enviar(s, evento, gravar = true) {
    evento.ts ||= Date.now();
    if (gravar) appendFileSync(path.join(pastaApp(s.nome), "conversa.jsonl"), JSON.stringify(evento) + "\n");
    const linha = `data: ${JSON.stringify(evento)}\n\n`;
    for (const res of s.clientes) res.write(linha);
  }

  function assinar(nome, res) {
    const s = sessao(nome);
    s.clientes.add(res);
    res.on("close", () => s.clientes.delete(res));
  }

  // Resumo amigável de cada ferramenta para a linha "o que o Claude está fazendo".
  function resumoFerramenta(nomeFerramenta, entrada, pastaProj) {
    const rel = (p) => {
      if (!p) return "";
      const r = path.relative(pastaProj, path.resolve(RAIZ, p));
      return r.startsWith("..") ? path.basename(p) : r.split(path.sep).join("/");
    };
    switch (nomeFerramenta) {
      case "Bash":
      case "PowerShell":
        return entrada.description || "Rodando um comando";
      case "Read":
        return `Lendo ${rel(entrada.file_path)}`;
      case "Write":
        return `Criando ${rel(entrada.file_path)}`;
      case "Edit":
        return `Editando ${rel(entrada.file_path)}`;
      case "Glob":
      case "Grep":
        return "Procurando nos arquivos";
      case "Skill":
        return `Seguindo o roteiro "${entrada.skill}"`;
      case "TodoWrite":
      case "TaskCreate":
      case "TaskUpdate":
        return "Organizando as próximas etapas";
      case "WebSearch":
        return `Pesquisando: ${entrada.query || ""}`;
      case "WebFetch":
        return "Lendo uma página da internet";
      case "Agent":
        return entrada.description || "Delegando uma subtarefa";
      case "AskUserQuestion":
        return "Esperando sua resposta";
      default:
        return nomeFerramenta;
    }
  }

  async function canUseTool(s, nomeFerramenta, entrada, { signal }) {
    if (nomeFerramenta !== "AskUserQuestion") return { behavior: "allow", updatedInput: entrada };
    const id = `p${Date.now()}`;
    const evento = { tipo: "pergunta", id, questions: entrada.questions || [] };
    const respostas = await new Promise((resolve, reject) => {
      s.pergunta = { id, evento, resolve };
      signal?.addEventListener("abort", () => reject(new Error("cancelado")));
      enviar(s, evento);
    }).finally(() => {
      s.pergunta = null;
    });
    enviar(s, { tipo: "resposta", id, answers: respostas });
    return { behavior: "allow", updatedInput: { ...entrada, answers: respostas } };
  }

  function responder(nome, id, answers) {
    const s = sessao(nome);
    if (!s.pergunta || s.pergunta.id !== id) return false;
    s.pergunta.resolve(answers);
    return true;
  }

  async function executar(s, texto, retomar) {
    const pastaProj = projetos.pastaProjeto(s.nome);
    const consulta = query({
      prompt: texto,
      options: {
        cwd: RAIZ,
        pathToClaudeCodeExecutable: executavelClaude(),
        settingSources: ["project"],
        systemPrompt: { type: "preset", preset: "claude_code", append: instrucoes(s.nome) },
        permissionMode: "default",
        canUseTool: (n, e, o) => canUseTool(s, n, e, o),
        disallowedTools: BLOQUEADAS,
        env: ambiente(),
        resume: retomar ? s.sessionId : undefined,
      },
    });
    s.consulta = consulta;
    const ferramentas = new Map();
    for await (const msg of consulta) {
      if (msg.session_id && msg.session_id !== s.sessionId) {
        s.sessionId = msg.session_id;
        writeFileSync(path.join(pastaApp(s.nome), "sessao.json"), JSON.stringify({ sessionId: s.sessionId }));
      }
      if (msg.type === "assistant" && !msg.parent_tool_use_id) {
        for (const bloco of msg.message.content || []) {
          if (bloco.type === "text" && bloco.text.trim()) {
            enviar(s, { tipo: "texto", texto: bloco.text });
          } else if (bloco.type === "tool_use") {
            const resumo = resumoFerramenta(bloco.name, bloco.input || {}, pastaProj);
            ferramentas.set(bloco.id, bloco);
            s.passo = resumo;
            if (bloco.name !== "AskUserQuestion") enviar(s, { tipo: "ferramenta", id: bloco.id, nome: bloco.name, resumo });
          }
        }
      } else if (msg.type === "user" && !msg.parent_tool_use_id && Array.isArray(msg.message?.content)) {
        for (const bloco of msg.message.content) {
          if (bloco.type !== "tool_result") continue;
          const uso = ferramentas.get(bloco.tool_use_id);
          if (bloco.is_error && uso?.name !== "AskUserQuestion") enviar(s, { tipo: "ferramenta_erro", id: bloco.tool_use_id });
          // Imagem lida dentro do projeto: mostra para a pessoa.
          const arq = uso?.name === "Read" ? uso.input?.file_path : null;
          if (arq && IMAGEM.test(arq) && !bloco.is_error) {
            const abs = path.resolve(RAIZ, arq);
            if (abs.startsWith(pastaProj + path.sep)) {
              enviar(s, { tipo: "imagem", caminho: path.relative(pastaProj, abs).split(path.sep).join("/") });
            }
          }
        }
      } else if (msg.type === "result") {
        if (s.interrompido) continue;
        enviar(s, {
          tipo: "fim",
          ok: msg.subtype === "success",
          erro: msg.subtype === "success" ? null : (msg.errors || []).join("\n") || msg.subtype,
          duracao: msg.duration_ms,
          custo: msg.total_cost_usd,
        });
      }
    }
  }

  async function mensagem(nome, texto, { oculto = false } = {}) {
    const s = sessao(nome);
    if (s.rodando) throw new Error("O Claude ainda está trabalhando neste projeto.");
    s.rodando = true;
    s.interrompido = false;
    s.passo = "Começando";
    if (!oculto) enviar(s, { tipo: "usuario", texto });
    enviar(s, { tipo: "estado", rodando: true }, false);
    (async () => {
      try {
        try {
          await executar(s, texto, Boolean(s.sessionId));
        } catch (e) {
          // Sessão antiga sumiu (outra máquina, pasta ~/.claude limpa): recomeça lendo o README.
          if (s.sessionId && /session|resume|conversation/i.test(String(e.message))) {
            s.sessionId = null;
            enviar(s, { tipo: "aviso", texto: "A conversa anterior não foi encontrada. O Claude vai retomar pelo README do projeto." });
            await executar(s, `Retome o projeto projetos/${nome} (leia o README dele primeiro).\n\n${texto}`, false);
          } else {
            throw e;
          }
        }
      } catch (e) {
        if (!s.interrompido && !/abort|cancel|interrupt/i.test(String(e.message)))
          enviar(s, { tipo: "erro", texto: String(e.message || e) });
      } finally {
        if (s.pergunta) enviar(s, { tipo: "pergunta_cancelada", id: s.pergunta.id });
        s.rodando = false;
        s.consulta = null;
        s.passo = null;
        s.pergunta = null;
        enviar(s, { tipo: "estado", rodando: false }, false);
      }
    })();
  }

  async function parar(nome) {
    const s = sessao(nome);
    if (!s.consulta) return;
    s.interrompido = true;
    enviar(s, { tipo: "aviso", texto: "Interrompido pela pessoa. Escreva abaixo para continuar." });
    try {
      await s.consulta.interrupt();
    } catch {}
  }

  return { assinar, historico, estado, mensagem, responder, parar };
}
