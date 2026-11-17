// Login na conta Claude pelo executável do Claude Code que vem junto com o Agent SDK.
// Sem terminal, `claude auth login` imprime um link; a pessoa autoriza no navegador, copia o
// código mostrado na página e cola na interface. O código vai para o stdin do processo.
import { execFile, spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const exec = promisify(execFile);
const AQUI = path.dirname(fileURLToPath(import.meta.url));

export function executavelClaude() {
  const nome = process.platform === "win32" ? "claude.exe" : "claude";
  const pacotes = [`claude-agent-sdk-${process.platform}-${process.arch}`];
  if (process.platform === "linux") pacotes.push(`claude-agent-sdk-${process.platform}-${process.arch}-musl`);
  for (const p of pacotes) {
    const c = path.join(AQUI, "..", "node_modules", "@anthropic-ai", p, nome);
    if (existsSync(c)) return c;
  }
  return "claude"; // Claude Code instalado no sistema
}

export async function status() {
  try {
    const { stdout } = await exec(executavelClaude(), ["auth", "status", "--json"], {
      timeout: 20000,
      windowsHide: true,
    });
    const s = JSON.parse(stdout);
    return {
      logado: Boolean(s.loggedIn) && s.authMethod !== "none",
      metodo: s.authMethod,
      email: s.email || null,
      organizacao: s.orgName || null,
      plano: s.subscriptionType || null,
      expira: s.loginExpiresAt || null,
    };
  } catch (e) {
    return { logado: false, erro: "Não foi possível consultar o login: " + (e.message || e) };
  }
}

let processo = null;

export function iniciar() {
  return new Promise((resolve) => {
    if (processo) {
      processo.kill();
      processo = null;
    }
    // BROWSER=true impede o Claude Code de tentar abrir o navegador sozinho: a interface abre o link.
    const p = spawn(executavelClaude(), ["auth", "login", "--claudeai"], {
      env: { ...process.env, BROWSER: process.platform === "win32" ? "" : "true" },
      windowsHide: true,
    });
    processo = p;
    let saida = "";
    let respondeu = false;
    const responder = (r) => {
      if (!respondeu) {
        respondeu = true;
        resolve(r);
      }
    };
    const ler = (d) => {
      saida += d.toString();
      const m = saida.match(/https:\/\/\S+oauth\/authorize\S+/);
      if (m) responder({ ok: true, url: m[0] });
    };
    p.stdout.on("data", ler);
    p.stderr.on("data", ler);
    p.on("exit", () => {
      if (processo === p) processo = null;
      responder({ ok: false, erro: saida.trim() || "O login terminou sem mostrar o link." });
    });
    setTimeout(() => responder({ ok: false, erro: "O link de login não apareceu em 30 s." }), 30000);
  });
}

export function enviarCodigo(codigo) {
  return new Promise((resolve) => {
    const p = processo;
    if (!p) return resolve({ ok: false, erro: "Clique em 'Entrar com a conta Claude' de novo." });
    let saida = "";
    p.stdout.on("data", (d) => (saida += d.toString()));
    p.stderr.on("data", (d) => (saida += d.toString()));
    const fim = setTimeout(() => resolve({ ok: false, erro: "Sem resposta do login em 60 s." }), 60000);
    p.on("exit", async (codigoSaida) => {
      clearTimeout(fim);
      const s = await status();
      resolve(s.logado ? { ok: true } : { ok: false, erro: saida.trim() || `Login falhou (código ${codigoSaida}).` });
    });
    p.stdin.write(codigo.trim() + "\n");
  });
}

export async function sair() {
  try {
    await exec(executavelClaude(), ["auth", "logout"], { timeout: 20000, windowsHide: true });
  } catch {}
  return status();
}
