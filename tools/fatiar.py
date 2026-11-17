#!/usr/bin/env python3
"""Fatia modelos (STL/3MF/OBJ) com o Bambu Studio pela linha de comando.

Os presets do Bambu Studio usam herança (`inherits`). O CLI não resolve essa
cadeia sozinho e fatia com valores faltando (peso 0 g, limites da máquina
ausentes). Este script resolve a herança, grava JSONs completos e chama o CLI.

Uso:
    python3 tools/fatiar.py projetos/x/saida/peca.stl
    python3 tools/fatiar.py a.stl b.stl --saida projetos/x/saida/fatiado --orientar
    python3 tools/fatiar.py peca.stl --processo "0.12mm Fine @BBL A1M" --filamento "Bambu PETG Basic @BBL A1M"
    python3 tools/fatiar.py base.stl logo.stl --multicor --filamento "Bambu PLA Basic @BBL A1M" \
        --filamento "Bambu PLA Matte @BBL A1M"   # 3MF com uma parte por cor; fatiar no Bambu Studio
    python3 tools/fatiar.py peca_pintada.3mf --filamento A --filamento B --cores "#D4A385,#101010"
        # 3MF com pintura por triângulo (tools/bl/pintura.py): o CLI fatia com troca de cor
    python3 tools/fatiar.py --listar processo   # lista presets compatíveis

Multicor (mais de um filamento): cada filamento recebe uma cor (--cores; sem isso o CLI 02.08
dá segfault ao fatiar 3MF pintado) e a torre de purga vai para --torre (a posição padrão do
preset fica fora da mesa da A1 mini).

Padrões vêm de config/impressora.json.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = json.loads((RAIZ / "config" / "impressora.json").read_text())
_CONF_PADRAO = (Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "BambuStudio"
                if os.name == "nt" else Path.home() / ".config" / "BambuStudio")
BAMBU_CONF = Path(os.environ.get("BAMBU_CONF", _CONF_PADRAO))
TIPOS = {"maquina": "machine", "processo": "process", "filamento": "filament"}


def achar_bambu():
    for candidato in (os.environ.get("BAMBU_STUDIO"), shutil.which("bambu-studio"),
                      str(Path.home() / ".local/bin/bambu-studio"),
                      r"C:\Program Files\Bambu Studio\bambu-studio.exe"):
        if candidato and Path(candidato).exists():
            return candidato
    sys.exit("ERRO: bambu-studio não encontrado. Defina BAMBU_STUDIO=/caminho/do/executavel.")


def indexar_presets():
    """Mapeia nome do preset -> arquivo. Presets do usuário têm prioridade."""
    indice = {}
    pastas = sorted((BAMBU_CONF / "system").glob("*/"))
    pastas += sorted((BAMBU_CONF / "user").glob("*/"))  # depois, para sobrescrever
    for pasta in pastas:
        for arquivo in pasta.rglob("*.json"):
            try:
                dados = json.loads(arquivo.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(dados, dict) and "name" in dados:
                indice[dados["name"]] = arquivo
    return indice


META_TEMPLATE = {"name", "instantiation", "type", "from", "setting_id", "version"}


def resolver(nome, indice, pilha=()):
    """Resolve `inherits` (pai) e `include` (templates). Ordem de prioridade, da menor para a
    maior: pai < templates incluídos < chaves do próprio preset.

    Desde a 02.08 os presets da Bambu trazem G-code de início/fim/troca de filamento/timelapse
    em templates via `include`. Ignorar o `include` faz o CLI usar o G-code genérico do
    `fdm_machine_common` (linha de purga fora da mesa da A1 mini, sem nivelamento/AMS).
    """
    if nome not in indice:
        sys.exit(f"ERRO: preset '{nome}' não encontrado em {BAMBU_CONF}. Use --listar.")
    if nome in pilha:
        sys.exit(f"ERRO: herança circular em '{nome}'.")
    dados = json.loads(indice[nome].read_text())
    pai = dados.pop("inherits", None)
    incluidos = dados.pop("include", None) or []
    if isinstance(incluidos, str):
        incluidos = [incluidos]
    base = resolver(pai, indice, pilha + (nome,)) if pai else {}
    for template in incluidos:
        extra = resolver(template, indice, pilha + (nome,))
        base.update({k: v for k, v in extra.items() if k not in META_TEMPLATE})
    base.update(dados)
    return base


def listar(tipo, indice):
    maquina = CONFIG["presets"]["maquina"]
    for nome, arquivo in sorted(indice.items()):
        dados = json.loads(arquivo.read_text())
        if dados.get("type") != TIPOS[tipo] or dados.get("instantiation") != "true":
            continue
        compat = dados.get("compatible_printers") or []
        if tipo == "maquina" or not compat or maquina in compat:
            print(nome)


def deslocar_stl(origem, destino, dx, dy):
    """Copia um STL binário somando (dx, dy) em todos os vértices."""
    import numpy as np
    dados = origem.read_bytes()
    n = int.from_bytes(dados[80:84], "little")
    if len(dados) != 84 + 50 * n:
        sys.exit(f"ERRO: {origem} não é STL binário (exporte com tools/bl/exportar.py)")
    tipo = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    tris = np.frombuffer(dados, dtype=tipo, count=n, offset=84).copy()
    tris["v"][:, :, 0] += dx
    tris["v"][:, :, 1] += dy
    destino.write_bytes(dados[:84] + tris.tobytes())
    return destino


def aplicar_ajustes(ajustes, processo, maquina, filamentos):
    """Aplica CHAVE=VALOR no preset que já tem a chave (filamento, máquina ou processo).

    Chave desconhecida vai para o processo. Valores em lista (um por extrusora/filamento)
    recebem o mesmo valor em todas as posições.
    """
    aplicados = {}
    for item in ajustes:
        if "=" not in item:
            sys.exit(f"ERRO: --ajuste espera CHAVE=VALOR, recebeu '{item}'")
        chave, valor = (parte.strip() for parte in item.split("=", 1))
        alvos = [f for f in filamentos if chave in f] or ([maquina] if chave in maquina else [processo])
        for alvo in alvos:
            atual = alvo.get(chave)
            alvo[chave] = [valor] * len(atual) if isinstance(atual, list) else valor
        aplicados[chave] = valor
    return aplicados


def conferir_ajustes(pasta, ajustes):
    """Lê o bloco de configuração no fim do G-code e confirma o valor de cada ajuste."""
    gcode = next(iter(sorted(pasta.glob("plate_*.gcode"))), None)
    if not gcode or not ajustes:
        return {}
    texto = gcode.read_text(errors="ignore")
    inicio, fim = texto.find("; CONFIG_BLOCK_START"), texto.find("; CONFIG_BLOCK_END")
    if inicio >= 0 and fim > inicio:
        texto = texto[inicio:fim]
    conferidos = {}
    for chave, valor in ajustes.items():
        achado = re.search(rf"^; {re.escape(chave)} = (.*)$", texto, re.M)
        efetivo = achado.group(1).strip() if achado else None
        conferidos[chave] = {"pedido": valor, "no_gcode": efetivo,
                             "ok": efetivo is not None and valor in efetivo.split(",")}
    return conferidos


def ler_cabecalho_gcode(pasta):
    resumo = {}
    padroes = {
        "tempo_total": r"^; total estimated time: (.+)$|; total estimated time: (.+)$",
        "filamento_g": r"^; total filament weight \[g\] : (.+)$",
        "filamento_m": r"^; total filament length \[mm\] : (.+)$",
        "camadas": r"^; total layer number: (.+)$",
    }
    for gcode in sorted(pasta.glob("plate_*.gcode")):
        texto = gcode.read_text(errors="ignore")[:20000]
        placa = {}
        for chave, padrao in padroes.items():
            achado = re.search(padrao, texto, re.M)
            if achado:
                placa[chave] = next(g for g in achado.groups() if g).strip()
        if "filamento_m" in placa:  # multicor: um valor por filamento, separados por vírgula
            placa["filamento_m"] = round(sum(float(x) for x in placa["filamento_m"].split(",")) / 1000, 2)
        trocas = re.search(r"^; total filament change: (\d+)", texto, re.M)
        if trocas:
            placa["trocas_de_filamento"] = int(trocas.group(1))
        resumo[gcode.stem] = placa
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modelos", nargs="*", help="arquivos STL/3MF/OBJ")
    p.add_argument("--saida", help="pasta de saída (padrão: <pasta do 1º modelo>/fatiado)")
    p.add_argument("--nome", help="nome do 3MF gerado (padrão: nome do 1º modelo)")
    p.add_argument("--maquina", default=CONFIG["presets"]["maquina"])
    p.add_argument("--processo", default=CONFIG["presets"]["processo"])
    p.add_argument("--filamento", action="append",
                   help="preset de filamento (repita para multicor; padrão do config)")
    p.add_argument("--multicor", action="store_true",
                   help="junta os modelos num objeto (uma parte por modelo, posições preservadas), "
                        "atribui filamentos e gera só o 3MF. Fatie no Bambu Studio: o CLI não faz troca de cor")
    p.add_argument("--ids-filamento",
                   help="com --multicor: filamento de cada modelo, na ordem (padrão: 1,2,3...)")
    p.add_argument("--cores", help="cor de cada filamento, na ordem: '#D4A385,#101010,...'")
    p.add_argument("--torre", default="130,110",
                   help="canto da torre de purga na mesa, 'X,Y' em mm (multicor; padrão 130,110)")
    p.add_argument("--placa", default=CONFIG["placa"], help="tipo de placa (ex.: 'Textured PEI Plate')")
    p.add_argument("--orientar", action="store_true", help="deixa o Bambu escolher a orientação")
    p.add_argument("--sem-arranjo", action="store_true", help="mantém posições XY do arquivo")
    p.add_argument("--so-3mf", action="store_true", help="gera projeto 3MF sem fatiar")
    p.add_argument("--ajuste", action="append", default=[], metavar="CHAVE=VALOR",
                   help="sobrescreve um parâmetro do preset (repita). Ex.: --ajuste seam_position=back "
                        "--ajuste sparse_infill_pattern=gyroid --ajuste wall_loops=3. Chaves e valores: "
                        ".claude/skills/configuracao-impressao/parametros-bambu.md")
    p.add_argument("--listar", choices=list(TIPOS), help="lista presets compatíveis e sai")
    args = p.parse_args()

    indice = indexar_presets()
    if args.listar:
        listar(args.listar, indice)
        return
    if not args.modelos:
        p.error("informe ao menos um modelo")

    modelos = [Path(m).resolve() for m in args.modelos]
    for m in modelos:
        if not m.exists():
            sys.exit(f"ERRO: arquivo não existe: {m}")
    saida = Path(args.saida).resolve() if args.saida else modelos[0].parent / "fatiado"
    perfis = saida / ".perfis"
    perfis.mkdir(parents=True, exist_ok=True)
    for antigo in [*saida.glob("plate_*.gcode"), saida / "result.json"]:
        antigo.unlink(missing_ok=True)

    maquina = resolver(args.maquina, indice)
    processo = resolver(args.processo, indice)
    processo["curr_bed_type"] = args.placa
    filamentos = [resolver(f, indice) for f in (args.filamento or [CONFIG["presets"]["filamento"]])]
    cores = args.cores.split(",") if args.cores else []
    if len(filamentos) > 1 and len(cores) < len(filamentos):
        padrao = ["#D4A385", "#101010", "#5A3A28", "#FFFFFF", "#0047AB", "#C0392B", "#2ECC71", "#F1C40F"]
        cores += padrao[len(cores):len(filamentos)]
    for fil, cor in zip(filamentos, cores):
        fil["filament_colour"] = [cor.strip()]
    if len(filamentos) > 1:
        tx, ty = (v.strip() for v in args.torre.split(","))
        processo["wipe_tower_x"], processo["wipe_tower_y"] = [tx], [ty]
    ajustes = aplicar_ajustes(args.ajuste, processo, maquina, filamentos)

    arquivos = {"maquina.json": maquina, "processo.json": processo}
    arquivos.update({f"filamento_{i}.json": f for i, f in enumerate(filamentos, 1)})
    for nome, dados in arquivos.items():
        (perfis / nome).write_text(json.dumps(dados, indent=1, ensure_ascii=False))

    if args.multicor:
        args.sem_arranjo = True
        args.so_3mf = True
        args.ids_filamento = args.ids_filamento or ",".join(
            str(min(i, len(filamentos))) for i in range(1, len(modelos) + 1))

    if args.sem_arranjo:
        # Modelos deste repo são centrados na origem; a mesa vai de 0 a X/Y.
        # Desloca para o centro da mesa mantendo as posições relativas (multicor).
        mesa = CONFIG["volume_util_mm"]
        modelos = [deslocar_stl(m, perfis / m.name, mesa["x"] / 2, mesa["y"] / 2)
                   if m.suffix.lower() == ".stl" else m for m in modelos]

    nome_3mf = (args.nome or modelos[0].stem) + ".3mf"
    cmd = [achar_bambu(), "--debug", "1",
           "--load-settings", f"{perfis/'maquina.json'};{perfis/'processo.json'}",
           "--load-filaments", ";".join(str(perfis / f"filamento_{i}.json") for i in range(1, len(filamentos) + 1)),
           "--arrange", "0" if args.sem_arranjo else "1",
           "--orient", "1" if args.orientar else "0",
           "--outputdir", str(saida),
           "--export-3mf", nome_3mf]
    if args.multicor:
        cmd += ["--assemble", "--load-filament-ids", args.ids_filamento]
    if not args.so_3mf:
        cmd += ["--slice", "0"]
    cmd += [str(m) for m in modelos]

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=saida)
    erros = [l for l in (proc.stdout + proc.stderr).splitlines()
             if "[error]" in l and "glfw" not in l.lower() and "display" not in l.lower()]

    resultado = {}
    arquivo_resultado = saida / "result.json"
    if arquivo_resultado.exists():
        resultado = json.loads(arquivo_resultado.read_text())

    (saida / nome_3mf).exists() or erros.append("3MF não foi gerado")
    if (saida / nome_3mf).exists():
        # sem isto a interface do Bambu mostra os valores do sistema (ver marcar_ajustes_3mf.py)
        sys.path.insert(0, str(RAIZ / "tools"))
        from marcar_ajustes_3mf import marcar
        marcar(saida / nome_3mf)
    conferidos = conferir_ajustes(saida, ajustes) or ajustes
    for chave, info in conferidos.items():
        if isinstance(info, dict) and not info["ok"]:
            erros.append(f"ajuste não aplicado: {chave}={info['pedido']} (no G-code: {info['no_gcode']}). "
                         "Chave ou valor inválido; o Bambu ignora em silêncio")
    resumo = {
        "ok": proc.returncode == 0 and resultado.get("return_code", 0) == 0 and (saida / nome_3mf).exists(),
        "codigo_saida": proc.returncode,
        "mensagem": resultado.get("error_string"),
        "projeto_3mf": str(saida / nome_3mf),
        "presets": {"maquina": args.maquina, "processo": args.processo,
                    "filamentos": [f["name"] for f in filamentos], "placa": args.placa},
        "ajustes": conferidos,
        "placas": ler_cabecalho_gcode(saida),
        "avisos": [p.get("warning_message") for p in resultado.get("sliced_plates", []) if p.get("warning_message")],
        "erros_cli": erros[-10:],
    }
    if args.so_3mf:
        resumo["proximo_passo"] = "3MF sem G-code: abra no Bambu Studio e fatie lá (tempo/peso aparecem após fatiar)"
        if args.multicor:
            resumo["filamento_por_modelo"] = dict(zip((m.name for m in modelos), args.ids_filamento.split(",")))
    for placa in resultado.get("sliced_plates", []):
        for obj in placa.get("objects", []):
            resumo.setdefault("objetos", []).append(
                {"nome": obj["name"], "bbox_mm": {k: round(obj["bbox"][k], 2) for k in ("width", "depth", "height")}})
    print(json.dumps(resumo, indent=2, ensure_ascii=False))
    sys.exit(0 if resumo["ok"] else 1)


if __name__ == "__main__":
    main()
