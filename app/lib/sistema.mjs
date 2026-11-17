// Detecta os programas que o fluxo precisa (Blender, Bambu Studio, Python, Git Bash no Windows)
// e prepara a pasta app/.atalhos com comandos curtos (blender, bambu-studio, python3) para o
// Claude usar quando o programa está instalado fora do PATH.
import { execFile } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, writeFileSync, chmodSync, statSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const exec = promisify(execFile);
export const WINDOWS = process.platform === "win32";
export const SISTEMA = WINDOWS ? "windows" : process.platform === "darwin" ? "macos" : "linux";

async function rodar(cmd, args, timeout = 15000) {
  try {
    const { stdout, stderr } = await exec(cmd, args, { timeout, windowsHide: true });
    return { ok: true, saida: (stdout || stderr || "").trim() };
  } catch (e) {
    return { ok: false, saida: (e.stderr || e.message || "").toString().trim() };
  }
}

function noPath(nome) {
  const exts = WINDOWS ? (process.env.PATHEXT || ".EXE;.CMD;.BAT").split(";") : [""];
  for (const pasta of (process.env.PATH || "").split(path.delimiter)) {
    for (const ext of exts) {
      const c = path.join(pasta, nome + ext.toLowerCase());
      if (pasta && existsSync(c)) return c;
      const C = path.join(pasta, nome + ext);
      if (pasta && existsSync(C)) return C;
    }
  }
  return null;
}

function primeiroQueExiste(lista) {
  return lista.find((c) => c && existsSync(c)) || null;
}

// Blender no Windows: C:\Program Files\Blender Foundation\Blender 5.x\blender.exe (pega a maior versão)
function blenderWindows() {
  const base = path.join(process.env.ProgramFiles || "C:\\Program Files", "Blender Foundation");
  if (!existsSync(base)) return null;
  const versoes = readdirSync(base)
    .filter((d) => existsSync(path.join(base, d, "blender.exe")))
    .sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
  return versoes.length ? path.join(base, versoes[0], "blender.exe") : null;
}

async function acharBlender() {
  const caminho = primeiroQueExiste([
    process.env.BLENDER,
    noPath("blender"),
    WINDOWS ? blenderWindows() : null,
    WINDOWS ? null : "/snap/bin/blender",
  ]);
  if (!caminho) return { ok: false, caminho: null, versao: null };
  const r = await rodar(caminho, ["--version"], 30000);
  const m = r.saida.match(/Blender\s+(\d+)\.(\d+)(?:\.(\d+))?/);
  const versao = m ? `${m[1]}.${m[2]}${m[3] ? "." + m[3] : ""}` : null;
  const maior = m ? Number(m[1]) : 0;
  return { ok: maior >= 5, caminho, versao, aviso: m && maior < 5 ? "Precisa do Blender 5.x ou mais novo" : null };
}

async function acharBambu() {
  const pf = process.env.ProgramFiles || "C:\\Program Files";
  const caminho = primeiroQueExiste([
    process.env.BAMBU_STUDIO,
    noPath("bambu-studio"),
    WINDOWS ? path.join(pf, "Bambu Studio", "bambu-studio.exe") : null,
    WINDOWS ? null : path.join(os.homedir(), ".local", "bin", "bambu-studio"),
  ]);
  const conf = WINDOWS
    ? path.join(process.env.APPDATA || path.join(os.homedir(), "AppData", "Roaming"), "BambuStudio")
    : path.join(os.homedir(), ".config", "BambuStudio");
  const presets = existsSync(path.join(conf, "system"));
  return {
    ok: Boolean(caminho) && presets,
    caminho,
    presets,
    aviso: caminho && !presets ? "Abra o Bambu Studio uma vez e escolha a impressora (para baixar os perfis)" : null,
  };
}

async function acharPython() {
  const candidatos = WINDOWS
    ? [["python", []], ["py", ["-3"]], ["python3", []]]
    : [["python3", []], ["python", []]];
  let semModulos = null;
  for (const [cmd, pre] of candidatos) {
    const caminho = noPath(cmd);
    if (!caminho) continue;
    const v = await rodar(caminho, [...pre, "--version"]);
    if (!v.ok || !/Python 3/.test(v.saida)) continue; // atalho da Microsoft Store não conta
    const mods = await rodar(caminho, [...pre, "-c", "import numpy, PIL; print('ok')"]);
    const info = { caminho, prefixo: pre, versao: v.saida.replace("Python ", "") };
    if (mods.ok) return { ok: true, ...info, modulos: true };
    semModulos ||= info;
  }
  if (semModulos) return { ok: false, ...semModulos, modulos: false, aviso: "Falta instalar Pillow e numpy" };
  return { ok: false, caminho: null, modulos: false };
}

async function acharGitBash() {
  if (!WINDOWS) return { ok: true, caminho: "/bin/bash", naoSeAplica: true };
  const pf = process.env.ProgramFiles || "C:\\Program Files";
  const caminho = primeiroQueExiste([
    process.env.CLAUDE_CODE_GIT_BASH_PATH,
    path.join(pf, "Git", "bin", "bash.exe"),
    path.join(os.homedir(), "AppData", "Local", "Programs", "Git", "bin", "bash.exe"),
  ]);
  return { ok: Boolean(caminho), caminho };
}

let cache = null;

export async function verificar(forcar = false) {
  if (cache && !forcar) return cache;
  const [blender, bambu, python, gitbash] = await Promise.all([
    acharBlender(),
    acharBambu(),
    acharPython(),
    acharGitBash(),
  ]);
  cache = {
    sistema: SISTEMA,
    node: { ok: true, versao: process.versions.node },
    blender,
    bambu,
    python,
    gitbash,
  };
  return cache;
}

// Cria app/.atalhos/<comando> apontando para o executável achado. Os scripts do repositório e as
// skills chamam `blender`, `bambu-studio` e `python3`; no Windows o Bash do Claude é o Git Bash,
// que roda esses atalhos sem extensão.
export function prepararAtalhos(pasta, info) {
  mkdirSync(pasta, { recursive: true });
  const escrever = (nome, alvo, prefixo = []) => {
    if (!alvo) return;
    const alvoBash = WINDOWS ? alvo.replace(/\\/g, "/") : alvo;
    const extra = prefixo.length ? " " + prefixo.join(" ") : "";
    const arq = path.join(pasta, nome);
    writeFileSync(arq, `#!/bin/sh\nexec "${alvoBash}"${extra} "$@"\n`);
    try {
      chmodSync(arq, 0o755);
    } catch {}
  };
  escrever("blender", info.blender.caminho);
  escrever("bambu-studio", info.bambu.caminho);
  if (info.python.caminho) escrever("python3", info.python.caminho, info.python.prefixo || []);
}

// Ambiente para o processo do Claude: atalhos na frente do PATH e variáveis lidas por
// tools/blender.sh (BLENDER) e tools/fatiar.py (BAMBU_STUDIO).
export function ambienteClaude(pastaAtalhos, info) {
  const env = { ...process.env };
  const chavePath = Object.keys(env).find((k) => k.toUpperCase() === "PATH") || "PATH";
  env[chavePath] = pastaAtalhos + path.delimiter + (env[chavePath] || "");
  if (info.blender.caminho) env.BLENDER = info.blender.caminho;
  if (info.bambu.caminho) env.BAMBU_STUDIO = info.bambu.caminho;
  if (WINDOWS && info.gitbash.caminho) env.CLAUDE_CODE_GIT_BASH_PATH = info.gitbash.caminho;
  // A chave de API não é usada: a interface só aceita login com a conta Claude.
  delete env.ANTHROPIC_API_KEY;
  return env;
}

export function modificado(caminho) {
  try {
    return statSync(caminho).mtimeMs;
  } catch {
    return 0;
  }
}
