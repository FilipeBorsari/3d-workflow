// Oficina 3D — interface (sem build). Rotas por hash: #/inicio, #/instalacao, #/login,
// #/projetos, #/novo, #/projeto/<nome>.

const tela = document.getElementById("tela");
let limparTela = null; // fecha o SSE ao sair da tela de projeto
const cache = { sistema: null, login: null };

// ---------- utilidades ----------
function h(tag, attrs = {}, ...filhos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v;
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const f of filhos.flat()) if (f != null && f !== false) el.append(f instanceof Node ? f : document.createTextNode(f));
  return el;
}

function escapar(t) {
  return String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

marked.use({ renderer: { html: (t) => escapar(t.text ?? t) }, breaks: true });
const md = (texto) => h("div", { class: "corpo", html: marked.parse(texto || "") });

async function api(caminho, opcoes = {}) {
  const r = await fetch(caminho, {
    ...opcoes,
    headers: opcoes.body && !(opcoes.body instanceof FormData) ? { "Content-Type": "application/json" } : undefined,
    body: opcoes.body && !(opcoes.body instanceof FormData) ? JSON.stringify(opcoes.body) : opcoes.body,
  });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dados.erro || `Erro ${r.status}`);
  return dados;
}

function tamanho(bytes) {
  if (bytes > 1e6) return (bytes / 1e6).toFixed(1) + " MB";
  return Math.max(1, Math.round(bytes / 1e3)) + " KB";
}

function quando(ms) {
  const d = new Date(ms);
  return d.toLocaleDateString("pt-BR") + " " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function arquivoUrl(nome, caminho, extra = "") {
  return `/arquivos/${encodeURIComponent(nome)}/${caminho.split("/").map(encodeURIComponent).join("/")}${extra}`;
}

function ampliar(src) {
  const caixa = document.getElementById("ampliada");
  caixa.querySelector("img").src = src;
  caixa.hidden = false;
}
document.getElementById("ampliada").addEventListener("click", (e) => {
  if (e.target.tagName !== "IMG") e.currentTarget.hidden = true;
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") document.getElementById("ampliada").hidden = true;
});

const PROGRAMAS_OBRIGATORIOS = (s) => ["blender", "bambu", "python", ...(s.sistema === "windows" ? ["gitbash"] : [])];

async function carregarSistema(forcar = false) {
  cache.sistema = await api("/api/sistema" + (forcar ? "?forcar=1" : ""));
  const falta = PROGRAMAS_OBRIGATORIOS(cache.sistema).some((k) => !cache.sistema[k].ok);
  document.getElementById("ponto-instalacao").className = "ponto " + (falta ? "falta" : "ok");
  return cache.sistema;
}

async function carregarLogin() {
  cache.login = await api("/api/login");
  document.getElementById("ponto-login").className = "ponto " + (cache.login.logado ? "ok" : "falta");
  return cache.login;
}

// ---------- tela: passo a passo ----------
async function telaInicio() {
  const [sis, log] = await Promise.all([cache.sistema || carregarSistema(), cache.login || carregarLogin()]);
  const programasOk = PROGRAMAS_OBRIGATORIOS(sis).every((k) => sis[k].ok);

  const passo = (n, titulo, conteudo, { feito = false, acao = null } = {}) =>
    h("li", { class: "passo" + (feito ? " feito" : "") },
      h("div", { class: "num" }, feito ? "✓" : String(n)),
      h("div", {}, h("h3", {}, titulo), conteudo),
      acao ? h("div", { class: "lado" }, acao) : h("div"));

  tela.replaceChildren(
    h("section", { class: "heroi" },
      h("h1", {}, "Da ideia ao arquivo pronto para imprimir"),
      h("p", {}, "A Oficina 3D junta uma IA que gera o modelo, o Claude que ajusta a peça para impressão no Blender, e o Bambu Studio que prepara a impressão. Siga os passos abaixo na ordem.")),
    h("ol", { class: "passos" },
      passo(1, "Instale os programas",
        h("p", {}, "Blender (modelagem), Bambu Studio (fatiador da impressora) e Python. A Oficina confere se cada um está instalado."),
        { feito: programasOk, acao: h("a", { class: "botao" + (programasOk ? "" : " principal"), href: "#/instalacao" }, programasOk ? "Ver programas" : "Instalar") }),
      passo(2, "Entre com sua conta Claude",
        h("p", {}, "Use uma conta Claude com plano pago (Pro, Max, Team ou Enterprise). O uso conta no limite do seu plano."),
        { feito: log.logado, acao: h("a", { class: "botao" + (log.logado ? "" : " principal"), href: "#/login" }, log.logado ? "Ver conta" : "Entrar") }),
      passo(3, "Gere o modelo 3D numa IA",
        h("div", {},
          h("p", {}, "Use uma IA que cria modelo 3D a partir de texto ou foto (por exemplo Meshy, Tripo ou o MakerLab da MakerWorld)."),
          h("ul", {},
            h("li", {}, "Descreva o objeto ou envie uma foto dele."),
            h("li", {}, "Baixe o resultado em ", h("strong", {}, ".3mf"), " (se a IA não tiver .3mf, serve .stl ou .obj)."),
            h("li", {}, "Guarde as fotos ou desenhos que você usou: eles viram as imagens de referência.")))),
      passo(4, "Crie o projeto e importe os arquivos",
        h("p", {}, "Dê um nome, conte o que você quer (tamanho, uso, cores) e envie o .3mf junto com as imagens de referência."),
        { acao: h("a", { class: "botao principal", href: "#/novo" }, "Novo projeto") }),
      passo(5, "Responda às perguntas do Claude",
        h("p", {}, "O Claude confere o modelo da IA e faz perguntas com opções (sabatina). Nada é modelado antes de você aprovar a especificação.")),
      passo(6, "Aprove a modelagem por etapas",
        h("p", {}, "Ele mostra imagens da peça em três etapas: forma base, detalhes e acabamento. Você aprova ou pede ajustes em cada uma.")),
      passo(7, "Abra no Bambu Studio e imprima",
        h("p", {}, "No fim aparece o arquivo .3mf pronto, já fatiado para a Bambu Lab A1 mini. Clique em \"Abrir no Bambu Studio\", confira e mande imprimir de lá."),
        { acao: h("a", { class: "botao", href: "#/projetos" }, "Meus projetos") })),
    h("p", { class: "sub", style: "margin-top:24px" },
      "Deixe aberta a janela preta (terminal) que iniciou a Oficina: fechar a janela desliga a Oficina."));
}

// ---------- tela: programas ----------
const INSTRUCOES = {
  blender: {
    titulo: "Blender 5",
    para: "Onde o Claude modela e confere a peça. Precisa ser a versão 5 ou mais nova.",
    linux: [
      ["Abra o terminal e rode:", "sudo snap install blender --classic"],
      ["Ou baixe em blender.org/download e coloque o comando ", "blender", " no PATH."],
    ],
    windows: [
      ["Baixe o instalador em ", { link: "https://www.blender.org/download/", texto: "blender.org/download" }, "."],
      ["Instale na pasta padrão (C:\\Program Files\\Blender Foundation). A Oficina acha sozinha."],
    ],
  },
  bambu: {
    titulo: "Bambu Studio",
    para: "Fatiador da impressora. A Oficina usa para gerar o arquivo de impressão e você usa para mandar imprimir.",
    linux: [
      ["Baixe o AppImage em ", { link: "https://bambulab.com/download/studio", texto: "bambulab.com/download/studio" }, "."],
      ["Crie o comando bambu-studio (troque o caminho do AppImage):", "mkdir -p ~/.local/bin\nprintf '#!/bin/sh\\nexec ~/Aplicativos/Bambu_Studio.AppImage \"$@\"\\n' > ~/.local/bin/bambu-studio\nchmod +x ~/.local/bin/bambu-studio ~/Aplicativos/Bambu_Studio.AppImage"],
      ["Abra o Bambu Studio uma vez, faça login se quiser e escolha a impressora Bambu Lab A1 mini (bico 0.4). Isso baixa os perfis de impressão."],
    ],
    windows: [
      ["Baixe o instalador em ", { link: "https://bambulab.com/download/studio", texto: "bambulab.com/download/studio" }, " e instale na pasta padrão."],
      ["Abra o Bambu Studio uma vez e escolha a impressora Bambu Lab A1 mini (bico 0.4). Isso baixa os perfis de impressão."],
    ],
  },
  python: {
    titulo: "Python 3 com Pillow e numpy",
    para: "Usado para fatiar pelo Bambu Studio e desenhar a folha de medidas.",
    linux: [["Abra o terminal e rode:", "sudo apt install python3 python3-pil python3-numpy"]],
    windows: [
      ["Baixe em ", { link: "https://www.python.org/downloads/", texto: "python.org/downloads" }, ". Na instalação, marque \"Add python.exe to PATH\"."],
      ["Depois abra o Prompt de Comando e rode:", "py -m pip install pillow numpy"],
    ],
  },
  gitbash: {
    titulo: "Git para Windows",
    para: "O Claude usa o Git Bash para rodar os scripts do Blender e do Bambu Studio.",
    soWindows: true,
    windows: [["Baixe em ", { link: "https://git-scm.com/download/win", texto: "git-scm.com/download/win" }, " e instale com as opções padrão."]],
  },
};

function linhaInstrucao(partes) {
  const li = h("li");
  for (const p of partes) {
    if (typeof p === "object") li.append(h("a", { href: p.link, target: "_blank", rel: "noopener" }, p.texto));
    else if (p.includes("\n") || /^(sudo|py |mkdir)/.test(p)) li.append(h("pre", {}, h("code", {}, p)));
    else if (p === "blender") li.append(h("code", {}, p));
    else li.append(p);
  }
  return li;
}

async function telaInstalacao() {
  const sis = cache.sistema || (await carregarSistema());
  let aba = sis.sistema === "windows" ? "windows" : "linux";

  const cartoes = h("div", { class: "grade" });
  const desenhar = () => {
    cartoes.replaceChildren();
    for (const [chave, inst] of Object.entries(INSTRUCOES)) {
      if (inst.soWindows && aba !== "windows") continue;
      const info = sis[chave];
      const daqui = (aba === "windows") === (sis.sistema === "windows");
      const selo = !daqui
        ? h("span", { class: "selo" }, "outro sistema")
        : info.ok
          ? h("span", { class: "selo ok" }, "Instalado" + (info.versao ? ` · ${info.versao}` : ""))
          : h("span", { class: "selo falta" }, info.aviso || "Não encontrado");
      cartoes.append(h("div", { class: "cartao programa" },
        h("div", { class: "cab" }, h("h3", {}, inst.titulo), selo),
        h("p", { class: "para" }, inst.para),
        daqui && info.ok ? null : h("ol", {}, (inst[aba] || []).map(linhaInstrucao)),
        daqui && info.caminho && !info.naoSeAplica ? h("div", { class: "caminho" }, info.caminho) : null));
    }
    cartoes.append(
      h("div", { class: "cartao programa" },
        h("div", { class: "cab" }, h("h3", {}, "Node.js"), h("span", { class: "selo ok" }, `Instalado · ${sis.node.versao}`)),
        h("p", { class: "para" }, "Roda a Oficina. Se você está vendo esta página, já está funcionando.")),
      h("div", { class: "cartao programa" },
        h("div", { class: "cab" }, h("h3", {}, "Claude Code"), h("span", { class: "selo ok" }, "Já incluído")),
        h("p", { class: "para" }, "Não precisa instalar: vem junto com a Oficina. Só falta entrar com a conta Claude."),
        h("div", {}, h("a", { class: "botao pequeno", href: "#/login" }, "Ir para o login"))));
  };

  const botaoAba = (id, rotulo) => h("button", { class: aba === id ? "ativo" : "", onclick: (e) => {
    aba = id;
    e.target.parentElement.querySelectorAll("button").forEach((b) => b.classList.toggle("ativo", b === e.target));
    desenhar();
  } }, rotulo);

  const verificar = h("button", { class: "botao", onclick: async (e) => {
    e.target.disabled = true;
    e.target.textContent = "Verificando…";
    await carregarSistema(true);
    telaInstalacao();
  } }, "Verificar de novo");

  desenhar();
  tela.replaceChildren(
    h("div", { class: "heroi" },
      h("h1", {}, "Programas necessários"),
      h("p", {}, "Instale o que estiver marcado como não encontrado e clique em \"Verificar de novo\". A Oficina procura nos lugares padrão de cada programa.")),
    h("div", { class: "acoes", style: "justify-content:space-between;margin-bottom:8px" },
      h("div", { class: "abas" }, botaoAba("linux", "Linux"), botaoAba("windows", "Windows")),
      verificar),
    cartoes);
}

// ---------- tela: login ----------
async function telaLogin() {
  const st = await carregarLogin();
  const caixa = h("div", { class: "cartao" });

  if (st.logado) {
    caixa.append(
      h("div", { class: "acoes", style: "justify-content:space-between" },
        h("h2", { style: "margin:0" }, "Conta conectada"), h("span", { class: "selo ok" }, "Conectado")),
      h("div", {},
        st.email ? h("div", {}, h("strong", {}, st.email)) : null,
        st.organizacao ? h("div", { class: "sub" }, st.organizacao) : null,
        st.plano ? h("div", { class: "sub" }, "Plano: " + st.plano) : null),
      h("div", { class: "acoes" },
        h("a", { class: "botao principal", href: "#/projetos" }, "Ir para os projetos"),
        h("button", { class: "botao", onclick: async (e) => {
          e.target.disabled = true;
          await api("/api/login/sair", { method: "POST" });
          telaLogin();
        } }, "Sair")));
  } else {
    const msg = h("div");
    const etapa2 = h("div", { class: "grade", hidden: true });
    const codigo = h("input", { type: "text", placeholder: "Cole aqui o código", autocomplete: "off" });
    const confirmar = h("button", { class: "botao principal", onclick: async () => {
      if (!codigo.value.trim()) return;
      confirmar.disabled = true;
      confirmar.textContent = "Conferindo…";
      const r = await api("/api/login/codigo", { method: "POST", body: { codigo: codigo.value } });
      if (r.ok) return telaLogin();
      msg.replaceChildren(h("div", { class: "aviso erro" }, r.erro));
      confirmar.disabled = false;
      confirmar.textContent = "Confirmar";
    } }, "Confirmar");
    const entrar = h("button", { class: "botao principal", onclick: async () => {
      entrar.disabled = true;
      entrar.textContent = "Preparando…";
      msg.replaceChildren();
      const r = await api("/api/login/iniciar", { method: "POST" });
      entrar.disabled = false;
      entrar.textContent = "Gerar novo link";
      if (!r.ok) return msg.replaceChildren(h("div", { class: "aviso erro" }, r.erro));
      window.open(r.url, "_blank", "noopener");
      etapa2.hidden = false;
      etapa2.querySelector("a.link-login").href = r.url;
      codigo.focus();
    } }, "Entrar com a conta Claude");

    etapa2.append(
      h("ol", { style: "margin:0;padding-left:1.2em" },
        h("li", {}, "Uma aba do Claude abriu. Se não abriu, ", h("a", { class: "link-login", href: "#", target: "_blank", rel: "noopener" }, "clique aqui"), "."),
        h("li", {}, "Entre na sua conta e clique em Autorizar."),
        h("li", {}, "Copie o código que aparece e cole abaixo.")),
      h("div", { class: "campo" }, h("label", {}, "Código de autorização"), codigo),
      h("div", { class: "acoes" }, confirmar));

    caixa.append(
      h("h2", { style: "margin:0" }, "Entrar com a conta Claude"),
      h("p", { class: "sub", style: "margin:0" }, "Precisa de uma conta Claude com plano pago (Pro, Max, Team ou Enterprise). O login fica salvo neste computador."),
      st.erro ? h("div", { class: "aviso erro" }, st.erro) : null,
      h("div", { class: "acoes" }, entrar),
      etapa2,
      msg);
  }

  tela.replaceChildren(h("div", { class: "login" },
    h("div", { class: "heroi" }, h("h1", {}, "Conta Claude"), h("p", {}, "O Claude é quem conversa com você, modela a peça e prepara a impressão.")),
    caixa));
}

// ---------- tela: projetos ----------
async function telaProjetos() {
  const lista = await api("/api/projetos");
  const grade = h("div", { class: "lista-projetos" });
  for (const p of lista) {
    grade.append(h("a", { class: "cartao projeto-cartao", href: `#/projeto/${encodeURIComponent(p.nome)}` },
      h("div", { class: "capa", style: p.capa ? `background-image:url("${arquivoUrl(p.nome, p.capa)}")` : "" }, p.capa ? "" : "sem imagem"),
      h("div", { class: "info" },
        h("strong", {}, p.titulo),
        p.status ? h("div", {}, h("span", { class: "selo" }, p.status)) : null,
        p.descricao ? h("span", {}, p.descricao) : null)));
  }
  tela.replaceChildren(
    h("div", { class: "acoes", style: "justify-content:space-between;margin-bottom:20px" },
      h("h1", { style: "margin:0" }, "Projetos"),
      h("a", { class: "botao principal", href: "#/novo" }, "+ Novo projeto")),
    lista.length ? grade : h("div", { class: "cartao" }, h("p", { class: "vazio" }, "Nenhum projeto ainda. Comece pelo botão Novo projeto.")));
}

// ---------- tela: novo projeto ----------
function slug(t) {
  return t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50);
}

function areaSoltar({ aceita, multiplo, titulo, dica, aoEscolher }) {
  const input = h("input", { type: "file", accept: aceita, multiple: multiplo, hidden: true, onchange: () => aoEscolher([...input.files]) });
  const area = h("div", { class: "soltar", tabindex: 0, onclick: () => input.click(), onkeydown: (e) => e.key === "Enter" && input.click() },
    h("strong", {}, titulo), h("div", {}, dica), input);
  area.addEventListener("dragover", (e) => { e.preventDefault(); area.classList.add("arrastando"); });
  area.addEventListener("dragleave", () => area.classList.remove("arrastando"));
  area.addEventListener("drop", (e) => {
    e.preventDefault();
    area.classList.remove("arrastando");
    aoEscolher([...e.dataTransfer.files]);
  });
  return area;
}

async function telaNovo() {
  const [log, sis] = await Promise.all([carregarLogin(), cache.sistema || carregarSistema()]);
  const faltam = PROGRAMAS_OBRIGATORIOS(sis).filter((k) => !sis[k].ok).map((k) => INSTRUCOES[k].titulo);

  let modelo = null;
  let imagens = [];
  let nomeEditado = false;

  const titulo = h("input", { type: "text", placeholder: "Ex.: Suporte de celular de mesa", oninput: () => { if (!nomeEditado) nome.value = slug(titulo.value); } });
  const nome = h("input", { type: "text", placeholder: "suporte-celular", oninput: () => (nomeEditado = true) });
  const objetivo = h("textarea", { placeholder: "Ex.: quero com 12 cm de altura, para ficar na mesa do escritório. Cor preta. A base precisa ser firme." });

  const infoModelo = h("div");
  const areaModelo = areaSoltar({
    aceita: ".3mf,.stl,.obj", multiplo: false,
    titulo: "Modelo 3D gerado pela IA", dica: "Arraste o arquivo .3mf aqui ou clique para escolher (.stl e .obj também servem)",
    aoEscolher: (arqs) => {
      modelo = arqs[0] || null;
      infoModelo.replaceChildren(modelo ? h("div", { class: "arquivo-escolhido" }, "📦 " + modelo.name + " · " + tamanho(modelo.size)) : "");
    },
  });
  areaModelo.append(infoModelo);

  const minis = h("div", { class: "miniaturas" });
  const desenharMinis = () => minis.replaceChildren(...imagens.map((f, i) => {
    const url = URL.createObjectURL(f);
    return h("figure", {}, h("img", { src: url, alt: f.name, title: f.name }),
      h("button", { type: "button", "aria-label": "Remover", onclick: (e) => { e.stopPropagation(); imagens.splice(i, 1); desenharMinis(); } }, "×"));
  }));
  const areaImagens = areaSoltar({
    aceita: "image/png,image/jpeg,image/webp", multiplo: true,
    titulo: "Imagens de referência", dica: "Fotos, desenhos ou a imagem que você usou na IA. Pode enviar várias.",
    aoEscolher: (arqs) => { imagens.push(...arqs.filter((f) => f.type.startsWith("image/"))); desenharMinis(); },
  });
  areaImagens.append(minis);

  const msg = h("div");
  const barra = h("div", { class: "barra", hidden: true }, h("div"));
  const enviar = h("button", { class: "botao principal", type: "submit", disabled: !log.logado }, "Criar projeto e começar");

  const form = h("form", { class: "form-novo", onsubmit: (e) => {
    e.preventDefault();
    msg.replaceChildren();
    if (!nome.value) return msg.replaceChildren(h("div", { class: "aviso erro" }, "Dê um nome ao projeto."));
    if (!modelo && !imagens.length) return msg.replaceChildren(h("div", { class: "aviso erro" }, "Envie o modelo 3D da IA ou pelo menos uma imagem de referência."));
    const dados = new FormData();
    dados.append("nome", nome.value);
    dados.append("descricao", titulo.value);
    dados.append("objetivo", objetivo.value);
    if (modelo) dados.append("modelo", modelo, modelo.name);
    for (const f of imagens) dados.append("imagens", f, f.name);

    enviar.disabled = true;
    enviar.textContent = "Enviando…";
    barra.hidden = false;
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/projetos");
    xhr.upload.onprogress = (ev) => { if (ev.lengthComputable) barra.firstChild.style.width = (100 * ev.loaded / ev.total).toFixed(0) + "%"; };
    xhr.onload = () => {
      const r = JSON.parse(xhr.responseText || "{}");
      if (r.ok) return (location.hash = `#/projeto/${encodeURIComponent(r.nome)}`);
      msg.replaceChildren(h("div", { class: "aviso erro" }, r.erro || "Não foi possível criar o projeto."));
      enviar.disabled = false;
      enviar.textContent = "Criar projeto e começar";
      barra.hidden = true;
    };
    xhr.onerror = () => { msg.replaceChildren(h("div", { class: "aviso erro" }, "Falha no envio.")); enviar.disabled = false; };
    xhr.send(dados);
  } },
    !log.logado ? h("div", { class: "aviso" }, "Entre com a conta Claude antes de criar o projeto. ", h("a", { href: "#/login" }, "Ir para o login")) : null,
    faltam.length ? h("div", { class: "aviso" }, `Faltam programas: ${faltam.join(", ")}. O Claude não vai conseguir modelar sem eles. `, h("a", { href: "#/instalacao" }, "Ver instalação")) : null,
    h("div", { class: "campo" }, h("label", {}, "O que é a peça?"), titulo),
    h("div", { class: "campo" }, h("label", {}, "Nome da pasta"), nome, h("div", { class: "dica" }, "Letras minúsculas, números e hífen. Preenchido sozinho a partir do título.")),
    h("div", { class: "campo" }, h("label", {}, "O que você quer?"), objetivo, h("div", { class: "dica" }, "Tamanho, onde vai ficar, cores, o que não pode faltar. O Claude pergunta o resto.")),
    areaModelo,
    areaImagens,
    barra,
    msg,
    h("div", { class: "acoes" }, enviar, h("a", { class: "botao", href: "#/projetos" }, "Cancelar")));

  tela.replaceChildren(
    h("div", { class: "heroi" }, h("h1", {}, "Novo projeto"), h("p", {}, "Envie o modelo que a IA gerou e as imagens de referência. O Claude começa a conferir o modelo assim que o projeto for criado.")),
    form);
}

// ---------- tela: projeto (conversa) ----------
async function telaProjeto(nome) {
  let dados;
  try {
    dados = await api(`/api/projetos/${encodeURIComponent(nome)}`);
  } catch (e) {
    tela.replaceChildren(h("div", { class: "aviso erro" }, e.message));
    return;
  }
  tela.classList.add("larga");

  const mensagens = h("div", { class: "mensagens" });
  const trabalhando = h("div", { class: "trabalhando", hidden: true }, h("div", { class: "giro" }), h("span", {}, "O Claude está trabalhando…"));
  const caixaTexto = h("textarea", { placeholder: "Escreva para o Claude… (Enter envia, Shift+Enter quebra linha)", rows: 1 });
  const botaoEnviar = h("button", { class: "botao principal" }, "Enviar");
  const botaoParar = h("button", { class: "botao", hidden: true }, "Parar");
  const painel = h("aside", { class: "painel" });

  let grupo = null; // bloco de passos (ferramentas) em sequência
  let rodando = false;
  const respondidas = new Set();
  const perguntasNaTela = new Map();

  const rolar = () => { mensagens.scrollTop = mensagens.scrollHeight; };
  const fecharGrupo = () => { grupo = null; };

  function setRodando(v, passo) {
    rodando = v;
    trabalhando.hidden = !v;
    botaoParar.hidden = !v;
    botaoEnviar.disabled = v;
    if (passo) trabalhando.lastChild.textContent = passo;
    else if (v) trabalhando.lastChild.textContent = "O Claude está trabalhando…";
  }

  function blocoRespondida(questions, answers) {
    return h("div", { class: "respondida" }, (questions || []).map((q) =>
      h("div", {}, h("strong", {}, (q.header || q.question) + ": "), String(answers?.[q.question] ?? "—"))));
  }

  function cartaoPergunta(ev) {
    const escolhas = ev.questions.map(() => ({ selecionadas: new Set(), outro: "" }));
    const botao = h("button", { class: "botao principal", disabled: true }, "Enviar respostas");
    const atualizar = () => { botao.disabled = !escolhas.every((e) => e.selecionadas.size || e.outro.trim()); };

    const blocos = ev.questions.map((q, iq) => {
      const tipo = q.multiSelect ? "checkbox" : "radio";
      const grupoNome = `${ev.id}-${iq}`;
      const outro = h("input", { type: "text", placeholder: "Outra resposta (escreva aqui)", oninput: () => {
        escolhas[iq].outro = outro.value;
        if (!q.multiSelect && outro.value.trim()) {
          escolhas[iq].selecionadas.clear();
          blocoEl.querySelectorAll("input[type=radio]").forEach((r) => (r.checked = false));
        }
        atualizar();
      } });
      const blocoEl = h("div", { class: "q" },
        q.header ? h("div", { class: "chip" }, q.header) : null,
        h("h3", {}, q.question),
        h("div", { class: "opcoes" },
          (q.options || []).map((op) => h("label", { class: "opcao" },
            h("input", { type: tipo, name: grupoNome, onchange: (e) => {
              const s = escolhas[iq].selecionadas;
              if (!q.multiSelect) { s.clear(); outro.value = ""; escolhas[iq].outro = ""; }
              e.target.checked ? s.add(op.label) : s.delete(op.label);
              atualizar();
            } }),
            h("div", {}, h("div", { class: "rotulo" }, op.label), op.description ? h("div", { class: "desc" }, op.description) : null),
            op.preview ? h("pre", { class: "previa" }, op.preview) : null)),
          outro));
      return blocoEl;
    });

    const cartao = h("div", { class: "pergunta" }, blocos, h("div", { class: "acoes" }, botao));
    botao.addEventListener("click", async () => {
      const answers = {};
      ev.questions.forEach((q, i) => {
        const partes = [...escolhas[i].selecionadas];
        if (escolhas[i].outro.trim()) partes.push(escolhas[i].outro.trim());
        answers[q.question] = partes.join(", ");
      });
      botao.disabled = true;
      botao.textContent = "Enviando…";
      try {
        const r = await api(`/api/projetos/${encodeURIComponent(nome)}/resposta`, { method: "POST", body: { id: ev.id, answers } });
        if (!r.ok) throw new Error("Esta pergunta não está mais esperando resposta.");
      } catch (e) {
        botao.textContent = e.message;
      }
    });
    return cartao;
  }

  function adicionar(ev, aoVivo) {
    switch (ev.tipo) {
      case "usuario":
        fecharGrupo();
        mensagens.append(h("div", { class: "msg pessoa" }, ev.texto));
        break;
      case "texto":
        fecharGrupo();
        mensagens.append(h("div", { class: "msg claude" }, md(ev.texto)));
        break;
      case "ferramenta": {
        if (!grupo) {
          grupo = { el: h("details", { class: "passos-claude" }, h("summary", {}), h("ul")), n: 0 };
          mensagens.append(grupo.el);
        }
        grupo.n++;
        grupo.el.querySelector("ul").append(h("li", { "data-id": ev.id }, ev.resumo));
        grupo.el.querySelector("summary").textContent = `${ev.resumo}${grupo.n > 1 ? `  ·  ${grupo.n} passos` : ""}`;
        if (aoVivo) setRodando(true, ev.resumo + "…");
        break;
      }
      case "ferramenta_erro": {
        const li = mensagens.querySelector(`li[data-id="${CSS.escape(ev.id)}"]`);
        if (li) { li.classList.add("falhou"); li.textContent += " (falhou, o Claude vai tentar de outro jeito)"; }
        break;
      }
      case "imagem": {
        fecharGrupo();
        const src = arquivoUrl(nome, ev.caminho, `?t=${ev.ts}`);
        mensagens.append(h("figure", { class: "msg claude msg-imagem" },
          h("img", { src, alt: ev.caminho, loading: "lazy", onclick: () => ampliar(src) }),
          h("figcaption", {}, ev.caminho)));
        if (aoVivo) atualizarPainel();
        break;
      }
      case "pergunta": {
        fecharGrupo();
        if (respondidas.has(ev.id)) break;
        const c = cartaoPergunta(ev);
        perguntasNaTela.set(ev.id, { el: c, ev });
        mensagens.append(c);
        if (aoVivo) trabalhando.lastChild.textContent = "Esperando sua resposta…";
        break;
      }
      case "resposta": {
        respondidas.add(ev.id);
        const p = perguntasNaTela.get(ev.id);
        if (p) { p.el.replaceWith(blocoRespondida(p.ev.questions, ev.answers)); perguntasNaTela.delete(ev.id); }
        break;
      }
      case "aviso":
        fecharGrupo();
        mensagens.append(h("div", { class: "msg aviso-msg" }, ev.texto));
        break;
      case "erro":
        fecharGrupo();
        mensagens.append(h("div", { class: "msg erro-msg" }, "Erro: " + ev.texto));
        break;
      case "fim":
        fecharGrupo();
        if (!ev.ok && ev.erro) mensagens.append(h("div", { class: "msg erro-msg" }, "O Claude parou com erro: " + ev.erro));
        if (aoVivo) atualizarPainel();
        break;
      case "pergunta_cancelada": {
        const p = perguntasNaTela.get(ev.id);
        if (p) { p.el.remove(); perguntasNaTela.delete(ev.id); }
        break;
      }
      case "estado":
        setRodando(ev.rodando);
        if (!ev.rodando) {
          // Sem Claude rodando não existe pergunta esperando resposta.
          for (const p of perguntasNaTela.values()) p.el.remove();
          perguntasNaTela.clear();
          atualizarPainel();
        }
        break;
      default:
        return;
    }
    rolar();
  }

  // Histórico: respostas aparecem depois das perguntas; marca antes para não desenhar cartões já respondidos.
  const perguntasHist = new Map();
  for (const ev of dados.historico) {
    if (ev.tipo === "resposta") respondidas.add(ev.id);
  }
  for (const ev of dados.historico) {
    if (ev.tipo === "pergunta") perguntasHist.set(ev.id, ev);
    if (ev.tipo === "resposta") {
      const q = perguntasHist.get(ev.id);
      fecharGrupo();
      if (q) mensagens.append(blocoRespondida(q.questions, ev.answers));
      continue;
    }
    if (ev.tipo === "pergunta" && respondidas.has(ev.id)) continue;
    if (ev.tipo === "pergunta" && !(dados.pergunta && dados.pergunta.id === ev.id)) continue; // ficou sem resposta (sessão parou)
    adicionar(ev, false);
  }
  if (!dados.historico.length && !dados.rodando) {
    mensagens.append(h("div", { class: "msg aviso-msg" }, "Projeto sem conversa na Oficina. Escreva abaixo para o Claude retomar (ele lê o README do projeto)."));
  }
  setRodando(dados.rodando, dados.passo ? dados.passo + "…" : null);

  // Painel lateral
  async function abrir(arquivo, programa, botao) {
    const original = botao.textContent;
    botao.disabled = true;
    try {
      await api(`/api/projetos/${encodeURIComponent(nome)}/abrir`, { method: "POST", body: { arquivo, programa } });
      botao.textContent = "Abrindo…";
    } catch (e) {
      botao.textContent = e.message;
    }
    setTimeout(() => { botao.disabled = false; botao.textContent = original; }, 2500);
  }

  function desenharPainel(d) {
    const prev = d.previews || [];
    const folha = prev.find((p) => p.nome === "folha.png");
    const outras = prev.filter((p) => p !== folha).slice(0, 8);
    const img = (p, grande) => {
      const src = arquivoUrl(nome, p.caminho, `?t=${p.modificado}`);
      return h("img", { src, alt: p.nome, title: p.nome, class: grande ? "grande" : "", loading: "lazy", onclick: () => ampliar(src) });
    };
    const botaoAbrir = (arquivo, programa, rotulo, principal) =>
      h("button", { class: "botao pequeno" + (principal ? " principal" : ""), onclick: (e) => abrir(arquivo, programa, e.currentTarget) }, rotulo);

    painel.replaceChildren(
      h("div", { class: "cartao" },
        h("h3", {}, "Arquivos para imprimir"),
        d.entregas.length
          ? h("ul", { class: "arquivos" }, d.entregas.map((a) => h("li", {},
              h("div", { class: "nome" }, a.caminho.replace(/^saida\//, "")),
              h("div", { class: "meta" }, `${tamanho(a.tamanho)} · ${quando(a.modificado)}`),
              h("div", { class: "acoes" },
                botaoAbrir(a.caminho, "bambu", "Abrir no Bambu Studio", true),
                h("a", { class: "botao pequeno", href: arquivoUrl(nome, a.caminho, "?baixar=1") }, "Baixar")))))
          : h("p", { class: "vazio" }, "Aparece aqui quando o Claude preparar o arquivo .3mf.")),
      h("div", { class: "cartao" },
        h("h3", {}, "Imagens da peça"),
        prev.length
          ? h("div", { class: "galeria" }, folha ? img(folha, true) : null, outras.map((p) => img(p, false)))
          : h("p", { class: "vazio" }, "As imagens aparecem quando o Claude gerar o modelo.")),
      h("div", { class: "cartao" },
        h("h3", {}, "Referências"),
        d.referencias.length
          ? h("div", { class: "galeria" }, d.referencias.map((r) => /\.(png|jpe?g|webp|gif)$/i.test(r.nome)
              ? img(r, false)
              : h("div", { class: "arquivos" }, h("div", { class: "nome" }, "📦 " + r.nome), botaoAbrir(r.caminho, "bambu", "Abrir no Bambu Studio"))))
          : h("p", { class: "vazio" }, "Sem referências.")),
      h("div", { class: "cartao" },
        h("h3", {}, "Mais"),
        h("div", { class: "acoes" },
          d.blend ? botaoAbrir(d.blend, "blender", "Abrir no Blender") : null,
          botaoAbrir(".", "pasta", "Abrir a pasta do projeto"))));
  }

  async function atualizarPainel() {
    try {
      desenharPainel(await api(`/api/projetos/${encodeURIComponent(nome)}`));
    } catch {}
  }

  async function enviarMensagem() {
    const texto = caixaTexto.value.trim();
    if (!texto || rodando) return;
    botaoEnviar.disabled = true;
    try {
      await api(`/api/projetos/${encodeURIComponent(nome)}/mensagem`, { method: "POST", body: { texto } });
      caixaTexto.value = "";
    } catch (e) {
      mensagens.append(h("div", { class: "msg erro-msg" }, e.message));
      botaoEnviar.disabled = false;
      rolar();
    }
  }
  botaoEnviar.addEventListener("click", enviarMensagem);
  caixaTexto.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarMensagem(); }
  });
  botaoParar.addEventListener("click", () => api(`/api/projetos/${encodeURIComponent(nome)}/parar`, { method: "POST" }));

  desenharPainel(dados);
  tela.replaceChildren(
    h("div", { class: "projeto-cab" },
      h("div", {}, h("a", { href: "#/projetos", class: "sub" }, "← Projetos"), h("h1", {}, dados.titulo)),
      dados.status ? h("span", { class: "selo" }, "Etapa: " + dados.status) : null),
    h("div", { class: "projeto" },
      h("section", { class: "cartao conversa" }, mensagens, trabalhando, h("div", { class: "entrada" }, caixaTexto, botaoParar, botaoEnviar)),
      painel));
  rolar();

  // Eventos ao vivo
  const fonte = new EventSource(`/api/projetos/${encodeURIComponent(nome)}/eventos`);
  fonte.onmessage = (m) => {
    const ev = JSON.parse(m.data);
    if (ev.tipo === "conectado") {
      setRodando(ev.rodando, ev.passo ? ev.passo + "…" : null);
      if (ev.pergunta && !perguntasNaTela.has(ev.pergunta.id) && !respondidas.has(ev.pergunta.id)) adicionar(ev.pergunta, true);
      return;
    }
    adicionar(ev, true);
  };
  limparTela = () => fonte.close();
}

// ---------- roteador ----------
async function rotear() {
  if (limparTela) { limparTela(); limparTela = null; }
  tela.classList.remove("larga");
  const [, rota, arg] = (location.hash || "#/inicio").match(/^#\/([^/]*)\/?(.*)$/) || [];
  document.querySelectorAll("#menu a").forEach((a) => a.classList.toggle("ativo", a.dataset.rota === rota || (rota === "projeto" || rota === "novo") && a.dataset.rota === "projetos"));
  tela.replaceChildren(h("p", { class: "sub" }, "Carregando…"));
  try {
    if (rota === "instalacao") await telaInstalacao();
    else if (rota === "login") await telaLogin();
    else if (rota === "projetos") await telaProjetos();
    else if (rota === "novo") await telaNovo();
    else if (rota === "projeto" && arg) await telaProjeto(decodeURIComponent(arg));
    else await telaInicio();
  } catch (e) {
    tela.replaceChildren(h("div", { class: "aviso erro" }, "Erro: " + e.message));
  }
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", rotear);
carregarSistema().catch(() => {});
carregarLogin().catch(() => {});
rotear();
