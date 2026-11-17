// Pastas de projeto (projetos/<nome>): listar, criar a partir de projetos/_modelo e montar o
// resumo que a interface mostra. Faz o mesmo que tools/novo_projeto.sh, mas em Node para
// funcionar também no Windows.
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

export const IMAGENS = [".png", ".jpg", ".jpeg", ".webp", ".gif"];
export const MODELOS = [".3mf", ".stl", ".obj"];

export function criarApi(RAIZ) {
  const PROJETOS = path.join(RAIZ, "projetos");

  // Caminho dentro de projetos/<nome>; recusa "..", links para fora e o modelo.
  function pastaProjeto(nome) {
    if (!nome || nome === "_modelo" || nome.includes("/") || nome.includes("\\") || nome.startsWith(".")) return null;
    const p = path.join(PROJETOS, nome);
    return existsSync(path.join(p, "README.md")) || existsSync(path.join(p, "modelo.py")) ? p : null;
  }

  function dentroDoProjeto(nome, relativo) {
    const base = pastaProjeto(nome);
    if (!base) return null;
    const alvo = path.resolve(base, relativo);
    if (alvo !== base && !alvo.startsWith(base + path.sep)) return null;
    return existsSync(alvo) ? alvo : null;
  }

  function lerReadme(base) {
    const arq = path.join(base, "README.md");
    if (!existsSync(arq)) return { titulo: path.basename(base), descricao: "", status: "" };
    const texto = readFileSync(arq, "utf8");
    const titulo = (texto.match(/^#\s+(.+)$/m) || [])[1] || path.basename(base);
    const linhas = texto.split("\n");
    const iTitulo = linhas.findIndex((l) => l.startsWith("# "));
    const descricao = (linhas.slice(iTitulo + 1).find((l) => l.trim() && !l.startsWith("-") && !l.startsWith("#")) || "").trim();
    const status = ((texto.match(/^-\s*Status:\s*([^<\n]+)/m) || [])[1] || "").trim();
    return { titulo, descricao: descricao === "DESCRICAO_CURTA" ? "" : descricao, status };
  }

  function arquivos(base, sub, exts) {
    const pasta = path.join(base, sub);
    if (!existsSync(pasta)) return [];
    return readdirSync(pasta)
      .filter((f) => exts.includes(path.extname(f).toLowerCase()))
      .map((f) => {
        const st = statSync(path.join(pasta, f));
        return { nome: f, caminho: path.posix.join(sub.split(path.sep).join("/"), f), tamanho: st.size, modificado: st.mtimeMs };
      })
      .sort((a, b) => b.modificado - a.modificado);
  }

  function capa(base) {
    const folha = path.join(base, "saida", "preview", "folha.png");
    if (existsSync(folha)) return "saida/preview/folha.png";
    const refs = arquivos(base, "referencias", IMAGENS);
    return refs.length ? refs[refs.length - 1].caminho : null;
  }

  function listar() {
    if (!existsSync(PROJETOS)) return [];
    return readdirSync(PROJETOS, { withFileTypes: true })
      .filter((d) => d.isDirectory() && d.name !== "_modelo" && !d.name.startsWith("."))
      .map((d) => {
        const base = path.join(PROJETOS, d.name);
        if (!pastaProjeto(d.name)) return null;
        let modificado = statSync(base).mtimeMs;
        for (const f of ["README.md", "modelo.py", path.join(".app", "conversa.jsonl")]) {
          if (existsSync(path.join(base, f))) modificado = Math.max(modificado, statSync(path.join(base, f)).mtimeMs);
        }
        return { nome: d.name, ...lerReadme(base), capa: capa(base), modificado };
      })
      .filter(Boolean)
      .sort((a, b) => b.modificado - a.modificado);
  }

  function detalhes(nome) {
    const base = pastaProjeto(nome);
    if (!base) return null;
    const entregas = [
      ...arquivos(base, "saida", [".3mf"]),
      ...arquivos(base, path.join("saida", "fatiado"), [".3mf"]),
    ].sort((a, b) => b.modificado - a.modificado);
    return {
      nome,
      pasta: base,
      ...lerReadme(base),
      previews: arquivos(base, path.join("saida", "preview"), IMAGENS),
      referencias: arquivos(base, "referencias", [...IMAGENS, ...MODELOS]),
      entregas,
      stls: arquivos(base, "saida", [".stl"]),
      blend: existsSync(path.join(base, "saida", "modelo.blend")) ? "saida/modelo.blend" : null,
    };
  }

  function nomeValido(nome) {
    return /^[a-z0-9]+(-[a-z0-9]+)*$/.test(nome);
  }

  function criar(nome, descricao) {
    if (!nomeValido(nome)) throw new Error("Nome inválido: use letras minúsculas, números e hífen (ex.: suporte-celular).");
    const destino = path.join(PROJETOS, nome);
    if (existsSync(destino)) throw new Error(`Já existe um projeto chamado "${nome}".`);
    cpSync(path.join(PROJETOS, "_modelo"), destino, { recursive: true });
    const saida = path.join(destino, "saida");
    if (existsSync(saida)) for (const f of readdirSync(saida)) rmSync(path.join(saida, f), { recursive: true, force: true });
    mkdirSync(path.join(destino, "referencias"), { recursive: true });
    mkdirSync(saida, { recursive: true });

    const modelo = path.join(destino, "modelo.py");
    if (existsSync(modelo)) {
      writeFileSync(
        modelo,
        readFileSync(modelo, "utf8").replace("NOME DO PROJETO", nome).replace("projetos/NOME/", `projetos/${nome}/`),
      );
    }
    const hoje = new Date().toISOString().slice(0, 10);
    const readme = path.join(destino, "README.md");
    writeFileSync(
      readme,
      readFileSync(readme, "utf8")
        .replace(/^# NOME DO PROJETO/m, `# ${nome}`)
        .replace(/^DESCRICAO_CURTA/m, () => (descricao || "Descreva o objetivo da peça.").replace(/\n+/g, " "))
        .replace(/^- Criado em: .*/m, `- Criado em: ${hoje}`),
    );
    return destino;
  }

  // Nome de arquivo seguro para referencias/: sem pastas, sem acento, sem caracteres estranhos.
  function nomeArquivo(original, usados) {
    const ext = path.extname(original).toLowerCase();
    let base = path
      .basename(original, path.extname(original))
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "arquivo";
    let nome = base + ext;
    for (let i = 2; usados.has(nome); i++) nome = `${base}-${i}${ext}`;
    usados.add(nome);
    return nome;
  }

  return { PROJETOS, pastaProjeto, dentroDoProjeto, listar, detalhes, criar, nomeArquivo, nomeValido };
}
