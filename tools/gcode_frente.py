#!/usr/bin/env python3
"""Imagem de frente de uma peça multicor COMO SAI IMPRESSA: paredes externas do G-code,
coloridas pelo filamento que o bico vai depositar.

A pintura de cor no Bambu Studio (e nos previews do Blender) mostra o que foi pintado; o
fatiador junta detalhes menores que a linha do bico (~0,45 mm no bico 0.4). Use esta imagem
para conferir textura fina (barba rala, pontilhado, cílios) antes de entregar.

Uso (Python do sistema):
    python3 tools/gcode_frente.py plate_1.gcode saida.png --cores "#D4A385,#101010,#5A3A28,#F4F4F4" \\
        [--centro 90,90] [--janela -15,15,0,24] [--titulo "texto"]

Valores negativos: use `--janela=-15,15,0,24` (com "=").
`--centro`: ponto da mesa onde está o centro (XY) da peça; `--janela`: x_min,x_max,z_min,z_max
em mm em volta desse centro. Desenha só a metade da frente (y < centro + 2 mm), vista de -Y.

Lê G1 e os arcos G2/G3 (o Bambu liga `enable_arc_fitting`: sem os arcos, partes inteiras da
parede somem da imagem e aparecem perímetros internos de outra cor por trás).
"""
import argparse
import re

import numpy as np
from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("gcode")
    p.add_argument("png")
    p.add_argument("--cores", required=True, help="cor de cada filamento, na ordem")
    p.add_argument("--centro", default="90,90")
    p.add_argument("--janela", default="-15,15,0,24")
    p.add_argument("--titulo", default="")
    p.add_argument("--escala", type=float, default=40.0, help="pixels por mm")
    a = p.parse_args()

    cores = {i: tuple(int(c.strip()[k:k + 2], 16) for k in (1, 3, 5))
             for i, c in enumerate(a.cores.split(","), 1)}
    cx, cy = (float(v) for v in a.centro.split(","))
    x_min, x_max, z_min, z_max = (float(v) for v in a.janela.split(","))
    esc = a.escala
    W, H = int((x_max - x_min) * esc), int((z_max - z_min) * esc)

    segs = []
    z, tipo, fer, x0, y0 = 0.0, "", 1, None, None
    altura = 0.2
    num = r"([-\d.]+)"
    for linha in open(a.gcode, errors="ignore"):
        m = re.match(r"^\s*T(\d+)\s*(;.*)?$", linha)   # T do G-code inicial vem com espaço antes
        if m and int(m.group(1)) < 16:
            fer = int(m.group(1)) + 1
        if linha.startswith("; Z_HEIGHT:"):
            z = float(linha.split(":")[1])
        elif linha.startswith("; LAYER_HEIGHT:"):
            altura = float(linha.split(":")[1])
        elif linha.startswith("; FEATURE:"):
            tipo = linha.split(":")[1].strip()
        elif linha.startswith(("G0", "G1", "G2", "G3")):
            cmd = linha[:2]
            mx, my = re.search(r"X" + num, linha), re.search(r"Y" + num, linha)
            if not mx and not my:
                continue
            x = float(mx.group(1)) - cx if mx else x0
            y = float(my.group(1)) - cy if my else y0
            if x0 is None or x is None or y is None:
                x0, y0 = x, y
                continue
            vale = (" E" in linha and tipo in ("Outer wall", "Overhang wall") and z_min <= z <= z_max)
            if vale:
                if cmd in ("G2", "G3"):
                    # arco (arc fitting do Bambu): I/J = centro relativo ao início
                    i = float(re.search(r"I" + num, linha).group(1))
                    j = float(re.search(r"J" + num, linha).group(1))
                    ccx, ccy = x0 + i, y0 + j
                    r = np.hypot(i, j)
                    a0, a1 = np.arctan2(y0 - ccy, x0 - ccx), np.arctan2(y - ccy, x - ccx)
                    if cmd == "G3" and a1 <= a0:
                        a1 += 2 * np.pi
                    if cmd == "G2" and a1 >= a0:
                        a1 -= 2 * np.pi
                    n = max(2, int(np.ceil(abs(a1 - a0) * r / 0.3)))
                    ang = np.linspace(a0, a1, n + 1)
                    pts = np.stack([ccx + r * np.cos(ang), ccy + r * np.sin(ang)], 1)
                else:
                    n = max(1, int(np.ceil(np.hypot(x - x0, y - y0) / 0.5)))
                    pts = np.stack([np.linspace(x0, x, n + 1), np.linspace(y0, y, n + 1)], 1)
                # pedaços curtos: a ordem de trás para a frente vale por pedaço, não pela linha longa
                for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
                    segs.append((xa, ya, xb, yb, z, altura, fer))
            x0, y0 = x, y
    segs = np.array(segs)
    segs = segs[np.argsort(-(segs[:, 1] + segs[:, 3]) / 2)]  # de trás para a frente

    img = Image.new("RGB", (W, H + 30), (200, 200, 200))
    d = ImageDraw.Draw(img)
    for xa, ya, xb, yb, zz, h, f in segs:
        if (ya + yb) / 2 > 2:
            continue
        u0, u1 = sorted(((xa - x_min) * esc, (xb - x_min) * esc))
        v = H - (zz - z_min) * esc + 30
        d.rectangle([u0, v - h * esc, max(u1, u0 + 1), v], fill=cores.get(int(f), (255, 0, 255)))
    d.text((8, 8), a.titulo, fill=(0, 0, 0))
    img.save(a.png)
    print(a.png)


if __name__ == "__main__":
    main()
