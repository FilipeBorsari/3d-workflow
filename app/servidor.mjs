// Oficina 3D: servidor local (só 127.0.0.1) da interface visual do fluxo de modelagem.
// Uso: node app/servidor.mjs  (ou iniciar.sh / iniciar.bat na raiz do repositório)
import Busboy from "busboy";
import { spawn } from "node:child_process";
import { createReadStream, createWriteStream, existsSync, statSync, unlinkSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as login from "./lib/login.mjs";
import { criarApi, IMAGENS, MODELOS } from "./lib/projetos.mjs";
import { criarSessoes } from "./lib/sessoes.mjs";
import { ambienteClaude, prepararAtalhos, verificar, WINDOWS } from "./lib/sistema.mjs";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, "..");
const PUBLICO = path.join(AQUI, "publico");
const ATALHOS = path.join(AQUI, ".atalhos");
const PORTA = Number(process.env.PORTA || 3333);
const LIMITE_UPLOAD = 300 * 1024 * 1024; // 300 MB por arquivo

const projetos = criarApi(RAIZ);
let infoSistema = await verificar();
prepararAtalhos(ATALHOS, infoSistema);
const sessoes = criarSessoes({ RAIZ, projetos, ambiente: () => ambienteClaude(ATALHOS, infoSistema) });

const TIPOS = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
  ".json": "application/json",
  ".3mf": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
  ".stl": "model/stl",
};

function json(res, codigo, dados) {
  res.writeHead(codigo, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(JSON.stringify(dados));
}

function lerJson(req) {
  return new Promise((resolve, reject) => {
    let corpo = "";
    req.on("data", (d) => {
      corpo += d;
      if (corpo.length > 1e6) req.destroy();
    });
    req.on("end", () => {
      try {
        resolve(corpo ? JSON.parse(corpo) : {});
      } catch (e) {
        reject(e);
      }
    });
  });
}

function servirArquivo(res, arquivo, baixar = false) {
  const st = statSync(arquivo);
  const cabecalho = {
    "Content-Type": TIPOS[path.extname(arquivo).toLowerCase()] || "application/octet-stream",
    "Content-Length": st.size,
    "Cache-Control": "no-cache",
  };
  if (baixar) cabecalho["Content-Disposition"] = `attachment; filename="${encodeURIComponent(path.basename(arquivo))}"`;
  res.writeHead(200, cabecalho);
  createReadStream(arquivo).pipe(res);
}

function abrirPrograma(programa, alvo) {
  let cmd;
  let args = [alvo];
  if (programa === "bambu") cmd = infoSistema.bambu.caminho;
  else if (programa === "blender") cmd = infoSistema.blender.caminho;
  else if (programa === "pasta") {
    const pasta = statSync(alvo).isDirectory() ? alvo : path.dirname(alvo);
    if (WINDOWS) [cmd, args] = ["explorer", [pasta]];
    else if (process.platform === "darwin") [cmd, args] = ["open", [pasta]];
    else [cmd, args] = ["xdg-open", [pasta]];
  }
  if (!cmd) throw new Error(programa === "bambu" ? "Bambu Studio não encontrado." : "Blender não encontrado.");
  // Bambu Studio muda a pasta de trabalho ao abrir: o caminho tem de ser absoluto (já é).
  const p = spawn(cmd, args, { detached: true, stdio: "ignore", windowsHide: false });
  p.on("error", () => {});
  p.unref();
}

function promptInicial(nome, { descricao, objetivo, modelo, imagens }) {
  const linhas = [
    `Projeto novo criado pela interface Oficina 3D: projetos/${nome}.`,
    "",
    `Descrição: ${descricao || "(não informada)"}`,
    `O que a pessoa quer: ${objetivo || "(não informado)"}`,
    modelo
      ? `Modelo 3D gerado por IA: projetos/${nome}/referencias/${modelo}`
      : "A pessoa não enviou modelo 3D gerado por IA.",
    imagens.length
      ? `Imagens de referência: ${imagens.map((i) => `projetos/${nome}/referencias/${i}`).join(", ")}`
      : "Sem imagens de referência.",
    "",
    "A interface já fez a F0 (pasta criada a partir de _modelo, referências copiadas). Siga o fluxo",
    "(skill fluxo-projeto) a partir daí:",
    modelo
      ? `1. Inspecione o modelo de IA: tools/blender.sh tools/inspecionar.py -- "projetos/${nome}/referencias/${modelo}" --saida projetos/${nome}/saida/inspecao_modelo_ia\n   Leia a folha.png gerada e o relatório (tamanho, malha fechada, partes soltas).`
      : "1. Veja as referências.",
    "2. Olhe as imagens de referência e compare com o modelo.",
    "3. Registre as referências no README e comece a sabatina (skill grill-me), uma pergunta por vez",
    "   com AskUserQuestion. Use o modelo de IA como ponto de partida da geometria, salvo se a pessoa disser outra coisa.",
  ];
  return linhas.join("\n");
}

function receberProjeto(req) {
  return new Promise((resolve, reject) => {
    const campos = {};
    const arquivos = [];
    const pendentes = [];
    let erro = null;
    const bb = Busboy({ headers: req.headers, limits: { fileSize: LIMITE_UPLOAD, files: 40 } });
    bb.on("field", (k, v) => (campos[k] = v));
    bb.on("file", (campo, stream, info) => {
      const temp = path.join(projetos.PROJETOS, `.upload-${Date.now()}-${arquivos.length}`);
      const registro = { campo, original: info.filename, temp, cortado: false };
      arquivos.push(registro);
      stream.on("limit", () => (registro.cortado = true));
      const destino = createWriteStream(temp);
      pendentes.push(new Promise((ok) => destino.on("close", ok)));
      stream.pipe(destino);
    });
    bb.on("error", (e) => (erro = e));
    bb.on("close", async () => {
      await Promise.all(pendentes);
      if (erro) return reject(erro);
      resolve({ campos, arquivos });
    });
    req.pipe(bb);
  });
}

async function criarProjeto(req, res) {
  const { campos, arquivos } = await receberProjeto(req);
  const limpar = () => arquivos.forEach((a) => existsSync(a.temp) && unlinkSync(a.temp));
  try {
    const nome = (campos.nome || "").trim();
    if (arquivos.some((a) => a.cortado)) throw new Error("Arquivo maior que 300 MB.");
    const modeloArq = arquivos.find((a) => a.campo === "modelo" && a.original);
    if (modeloArq && !MODELOS.includes(path.extname(modeloArq.original).toLowerCase()))
      throw new Error("O modelo 3D precisa ser .3mf, .stl ou .obj.");
    const imagens = arquivos.filter((a) => a.campo === "imagens" && a.original);
    for (const i of imagens)
      if (!IMAGENS.includes(path.extname(i.original).toLowerCase()))
        throw new Error(`"${i.original}" não é imagem (.png, .jpg, .webp).`);

    const destino = projetos.criar(nome, campos.descricao);
    const usados = new Set();
    const { renameSync, copyFileSync } = await import("node:fs");
    const mover = (a) => {
      const final = projetos.nomeArquivo(a.original, usados);
      const alvo = path.join(destino, "referencias", final);
      try {
        renameSync(a.temp, alvo);
      } catch {
        copyFileSync(a.temp, alvo);
        unlinkSync(a.temp);
      }
      return final;
    };
    const modelo = modeloArq ? mover(modeloArq) : null;
    const nomesImagens = imagens.map(mover);
    limpar();
    await sessoes.mensagem(
      nome,
      promptInicial(nome, { descricao: campos.descricao, objetivo: campos.objetivo, modelo, imagens: nomesImagens }),
      { oculto: true },
    );
    json(res, 200, { ok: true, nome });
  } catch (e) {
    limpar();
    json(res, 400, { ok: false, erro: e.message });
  }
}

async function rotas(req, res) {
  const url = new URL(req.url, "http://localhost");
  const p = decodeURIComponent(url.pathname);
  const m = req.method;

  if (p === "/api/sistema" && m === "GET") {
    if (url.searchParams.has("forcar")) {
      infoSistema = await verificar(true);
      prepararAtalhos(ATALHOS, infoSistema);
    }
    return json(res, 200, infoSistema);
  }
  if (p === "/api/login" && m === "GET") return json(res, 200, await login.status());
  if (p === "/api/login/iniciar" && m === "POST") return json(res, 200, await login.iniciar());
  if (p === "/api/login/codigo" && m === "POST") {
    const { codigo } = await lerJson(req);
    return json(res, 200, await login.enviarCodigo(codigo || ""));
  }
  if (p === "/api/login/sair" && m === "POST") return json(res, 200, await login.sair());

  if (p === "/api/projetos" && m === "GET") return json(res, 200, projetos.listar());
  if (p === "/api/projetos" && m === "POST") return criarProjeto(req, res);

  let r = p.match(/^\/api\/projetos\/([^/]+)(?:\/(\w+))?$/);
  if (r) {
    const [, nome, acao] = r;
    if (!projetos.pastaProjeto(nome)) return json(res, 404, { erro: "Projeto não encontrado." });
    if (!acao && m === "GET")
      return json(res, 200, { ...projetos.detalhes(nome), ...sessoes.estado(nome), historico: sessoes.historico(nome) });
    if (acao === "eventos" && m === "GET") {
      res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-store", Connection: "keep-alive" });
      res.write(`data: ${JSON.stringify({ tipo: "conectado", ...sessoes.estado(nome) })}\n\n`);
      sessoes.assinar(nome, res);
      const ping = setInterval(() => res.write(": ping\n\n"), 20000);
      res.on("close", () => clearInterval(ping));
      return;
    }
    if (acao === "mensagem" && m === "POST") {
      const { texto } = await lerJson(req);
      if (!texto?.trim()) return json(res, 400, { erro: "Mensagem vazia." });
      try {
        await sessoes.mensagem(nome, texto.trim());
        return json(res, 200, { ok: true });
      } catch (e) {
        return json(res, 409, { erro: e.message });
      }
    }
    if (acao === "resposta" && m === "POST") {
      const { id, answers } = await lerJson(req);
      return json(res, 200, { ok: sessoes.responder(nome, id, answers || {}) });
    }
    if (acao === "parar" && m === "POST") {
      await sessoes.parar(nome);
      return json(res, 200, { ok: true });
    }
    if (acao === "abrir" && m === "POST") {
      const { arquivo, programa } = await lerJson(req);
      const alvo = projetos.dentroDoProjeto(nome, arquivo || ".");
      if (!alvo) return json(res, 404, { erro: "Arquivo não encontrado." });
      try {
        abrirPrograma(programa, alvo);
        return json(res, 200, { ok: true });
      } catch (e) {
        return json(res, 400, { erro: e.message });
      }
    }
  }

  r = p.match(/^\/arquivos\/([^/]+)\/(.+)$/);
  if (r && m === "GET") {
    const alvo = projetos.dentroDoProjeto(r[1], r[2]);
    if (!alvo || statSync(alvo).isDirectory()) return json(res, 404, { erro: "Arquivo não encontrado." });
    return servirArquivo(res, alvo, url.searchParams.has("baixar"));
  }

  if (p === "/vendor/marked.js") return servirArquivo(res, path.join(AQUI, "node_modules", "marked", "lib", "marked.umd.js"));

  const estatico = path.resolve(PUBLICO, "." + (p === "/" ? "/index.html" : p));
  if (estatico.startsWith(PUBLICO + path.sep) && existsSync(estatico) && statSync(estatico).isFile())
    return servirArquivo(res, estatico);
  json(res, 404, { erro: "Não encontrado." });
}

const servidor = http.createServer((req, res) => {
  // Só aceita páginas servidas por este servidor (bloqueia outro site chamando a API local).
  const origem = req.headers.origin;
  if (req.method !== "GET" && origem && !/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(origem)) {
    return json(res, 403, { erro: "Origem não permitida." });
  }
  rotas(req, res).catch((e) => {
    console.error(e);
    if (!res.headersSent) json(res, 500, { erro: String(e.message || e) });
  });
});

servidor.listen(PORTA, "127.0.0.1", () => {
  console.log(`Oficina 3D rodando em http://localhost:${PORTA}`);
  console.log("Para parar: Ctrl+C nesta janela.");
});
