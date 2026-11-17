#!/usr/bin/env python3
"""Marca no 3MF do Bambu quais ajustes diferem dos perfis de sistema (`different_settings_to_system`).

Por quê: o 3MF gerado pelo CLI (tools/fatiar.py, tools/mesas.py) sai com esse campo vazio. A
interface do Bambu Studio lê "vazio" como "projeto igual ao perfil de sistema" e, ao abrir, mostra
os valores do sistema: no Asta (2026-11-11) apareceram 2 paredes, suporte desligado e torre de
purga ligada, embora o projeto tivesse 3 paredes, suporte e torre desligada. O G-code embutido
estava certo, mas fatiar de novo na interface jogava fora os ajustes.

Este script compara o `Metadata/project_settings.config` com os perfis de sistema resolvidos
(processo, cada filamento, impressora) e grava a lista de chaves alteradas, separadas por ";",
na ordem [processo, filamento 1..N, impressora]. O resto do 3MF (G-code incluído) não muda.

Uso (Python do sistema):
    python3 tools/marcar_ajustes_3mf.py projeto.3mf [outro.3mf ...]
"""
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("fatiar", RAIZ / "tools" / "fatiar.py")
fatiar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fatiar)

CONFIG = "Metadata/project_settings.config"
IGNORAR = {"name", "inherits", "include", "from", "setting_id", "instantiation", "version", "type",
           "compatible_printers", "compatible_printers_condition", "compatible_prints",
           "compatible_prints_condition", "print_settings_id", "printer_settings_id",
           "filament_settings_id", "different_settings_to_system", "filament_id", "description"}


def _lista(v):
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def diferencas(projeto, preset, indice=None):
    """Chaves do preset cujo valor no projeto é outro. `indice`: posição do filamento nas listas
    por filamento do projeto (None = comparar a lista inteira)."""
    chaves = []
    for k, v in preset.items():
        if k in IGNORAR or k not in projeto:
            continue
        p, s = _lista(projeto[k]), _lista(v)
        if indice is not None and len(p) > indice and len(s) == 1:
            p = [p[indice]]
        if p != s:
            chaves.append(k)
    return sorted(chaves)


def marcar(caminho):
    caminho = Path(caminho)
    with zipfile.ZipFile(caminho) as z:
        arquivos = {n: z.read(n) for n in z.namelist()}
    cfg = json.loads(arquivos[CONFIG])
    idx = fatiar.indexar_presets()
    processo = diferencas(cfg, fatiar.resolver(cfg["print_settings_id"], idx))
    filamentos = [diferencas(cfg, fatiar.resolver(nome, idx), i)
                  for i, nome in enumerate(cfg["filament_settings_id"])]
    impressora = diferencas(cfg, fatiar.resolver(cfg["printer_settings_id"], idx))
    cfg["different_settings_to_system"] = [";".join(processo), *(";".join(f) for f in filamentos),
                                           ";".join(impressora)]
    arquivos[CONFIG] = json.dumps(cfg, indent=4, ensure_ascii=False).encode()
    temp = caminho.with_suffix(".tmp.3mf")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in arquivos.items():
            z.writestr(n, d)
    temp.replace(caminho)
    return {"processo": processo, "filamentos": filamentos, "impressora": impressora}


if __name__ == "__main__":
    for arq in sys.argv[1:]:
        r = marcar(arq)
        print(f"{arq}\n  processo ({len(r['processo'])}): {', '.join(r['processo'])}")
        for i, f in enumerate(r["filamentos"], 1):
            print(f"  filamento {i} ({len(f)}): {', '.join(f)}")
        print(f"  impressora ({len(r['impressora'])}): {', '.join(r['impressora'])}")
