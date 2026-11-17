"""Monta e fatia um projeto do Bambu Studio com várias mesas já arrumadas (entrega em 3MF).

Usa `--load-assemble-list` do CLI: cada mesa tem nome e peças com posição (centro da peça na
mesa, mm), filamento e ajustes por objeto. Generaliza projetos/caneca-jo-spinola/montar_mesas_v2.py
(peças de uma cor só, sem objeto montado). Rodar com o Python do sistema:

    from mesas import montar
    montar(pasta_saida, "nome", mesas=[("1 - corpo", [(stl, 1, (70, 128), {"wall_loops": "3"})])],
           maquina="Bambu Lab A1 0.4 nozzle", processo="0.20mm Standard @BBL A1",
           filamentos=[("Bambu PLA Basic @BBL A1", "#2B2B2B")])

Item de mesa: (arquivo, filamento, (x, y), ajustes[, centralizar=True[, grupo=0]]); com centralizar=False,
(x, y) soma direto às coordenadas do arquivo (peças que já estão na posição relativa certa, como
uma figura montada em várias peças). grupo >= 1 junta os itens de mesmo grupo num objeto só, de
várias partes (o Bambu apoia cada OBJETO na mesa ao abrir; objetos soltos de uma figura montada
caem para z = 0). `fatiar_agora=False` só gera o 3MF.
A peça pode ser STL ou 3MF (ex.: 3MF pintado por tools/bl/pintura.py, que o CLI fatia com troca de
cor). A posição dada é o centro da peça na mesa; o fundo vai para z = 0.
"""
import importlib.util
import json
import struct
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("fatiar", RAIZ / "tools" / "fatiar.py")
fatiar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fatiar)


def caixa(caminho):
    """(min, max) de um STL binário ou de um 3MF (todos os vértices)."""
    if str(caminho).lower().endswith(".3mf"):
        import re
        import zipfile
        import numpy as np
        with zipfile.ZipFile(caminho) as z:
            nomes = [n for n in z.namelist() if n.lower().endswith(".model")]
            v = np.array(re.findall(rb'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"',
                                    b"".join(z.read(n) for n in nomes)), dtype=float)
        return tuple(v.min(0)), tuple(v.max(0))
    return caixa_stl(caminho)


def caixa_stl(caminho):
    """(min, max) do STL binário, para conferir se está centrado."""
    dados = Path(caminho).read_bytes()
    n = struct.unpack("<I", dados[80:84])[0]
    xs, ys, zs = [], [], []
    for i in range(n):
        v = struct.unpack("<9f", dados[84 + 50 * i + 12:84 + 50 * i + 48])
        xs += v[0::3]; ys += v[1::3]; zs += v[2::3]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def montar(saida, nome, mesas, maquina, processo, filamentos, ajustes_processo=None, fatiar_agora=True):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    perfis = saida / ".perfis"
    perfis.mkdir(exist_ok=True)
    for antigo in [*saida.glob("plate_*.gcode"), saida / "result.json"]:
        antigo.unlink(missing_ok=True)

    indice = fatiar.indexar_presets()
    perfil_maquina = fatiar.resolver(maquina, indice)
    perfil_processo = fatiar.resolver(processo, indice)
    perfil_processo["curr_bed_type"] = fatiar.CONFIG["placa"]
    perfil_processo.update(ajustes_processo or {})
    (perfis / "maquina.json").write_text(json.dumps(perfil_maquina, indent=1, ensure_ascii=False))
    (perfis / "processo.json").write_text(json.dumps(perfil_processo, indent=1, ensure_ascii=False))
    arquivos_fil = []
    for i, (preset, cor) in enumerate(filamentos, 1):
        fil = fatiar.resolver(preset, indice)
        fil["filament_colour"] = [cor]
        caminho = perfis / f"filamento_{i}.json"
        caminho.write_text(json.dumps(fil, indent=1, ensure_ascii=False))
        arquivos_fil.append(caminho)

    lista = {"plates": []}
    for nome_mesa, pecas in mesas:
        objetos = []
        for item in pecas:
            stl, filamento, (x, y), ajustes = item[:4]
            centralizar = item[4] if len(item) > 4 else True
            grupo = item[5] if len(item) > 5 else 0   # >= 1: junta num objeto de várias partes
            (x0, y0, z0), (x1, y1, _) = caixa(stl)
            dx, dy, dz = ((x - (x0 + x1) / 2, y - (y0 + y1) / 2, -z0) if centralizar else (x, y, 0.0))
            objetos.append({"path": str(Path(stl).resolve()), "count": 1, "filaments": [filamento],
                            "assemble_index": [grupo], "pos_x": [float(dx)], "pos_y": [float(dy)],
                            "pos_z": [float(dz)], "print_params": ajustes})
        lista["plates"].append({"plate_name": nome_mesa, "need_arrange": False, "objects": objetos})
    (saida / "montagem.json").write_text(json.dumps(lista, indent=1, ensure_ascii=False))

    cmd = [fatiar.achar_bambu(), "--debug", "1",
           "--load-settings", f"{perfis / 'maquina.json'};{perfis / 'processo.json'}",
           "--load-filaments", ";".join(str(c) for c in arquivos_fil),
           "--load-assemble-list", str(saida / "montagem.json"),
           "--outputdir", str(saida), "--export-3mf", f"{nome}.3mf"] + (["--slice", "0"] if fatiar_agora else [])
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=saida)
    erros = [l for l in (proc.stdout + proc.stderr).splitlines()
             if "[error]" in l and "glfw" not in l.lower() and "display" not in l.lower()]
    resultado = json.loads((saida / "result.json").read_text()) if (saida / "result.json").exists() else {}
    if (saida / f"{nome}.3mf").exists():
        # sem isto a interface do Bambu mostra os valores do sistema (ver marcar_ajustes_3mf.py)
        import sys
        sys.path.insert(0, str(RAIZ / "tools"))
        from marcar_ajustes_3mf import marcar
        marcar(saida / f"{nome}.3mf")
    maquina_curta = perfil_maquina.get("printer_model", "").replace("Bambu Lab ", "")
    gcodes = sorted(saida.glob("plate_*.gcode"))
    gcode_da_maquina = bool(gcodes) and all(
        f";===== machine: {maquina_curta} " in g.read_text(errors="ignore")[:200000] for g in gcodes)

    resumo = {"ok": proc.returncode == 0 and resultado.get("return_code", 1) == 0 and gcode_da_maquina,
              "projeto_3mf": str(saida / f"{nome}.3mf"), "maquina": maquina, "processo": processo,
              "filamentos": [f"{p} {c}" for p, c in filamentos],
              "gcode_da_maquina": gcode_da_maquina, "mesas": [], "erros_cli": erros[-10:]}
    for placa, (nome_mesa, _) in zip(resultado.get("sliced_plates", []), mesas):
        segundos = placa.get("total_predication", 0)
        resumo["mesas"].append({
            "mesa": nome_mesa,
            "tempo": f"{int(segundos // 3600)}h {int(segundos % 3600 // 60)}min",
            "segundos": segundos,
            "gramas": round(sum(f.get("total_used_g", 0) for f in placa.get("filaments", [])), 1),
            "aviso": placa.get("warning_message") or None,
            "objetos": [o["name"] for o in placa.get("objects", [])]})
    print(json.dumps(resumo, indent=2, ensure_ascii=False))
    return resumo
