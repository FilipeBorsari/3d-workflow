"""Corta um STL binário em planos e lista os contornos (medir peças de terceiros).

Uso (Python do sistema):
    python3 tools/cortar_stl.py peca.stl 1 5 10            # cortes em Z = 1, 5 e 10 mm
    python3 tools/cortar_stl.py peca.stl 0 --eixo x        # corte no plano X = 0
    python3 tools/cortar_stl.py peca.stl 2 8 --png cortes.png   # desenha os cortes numa imagem

Para cada corte imprime os contornos (fechados) do maior para o menor: tamanho nos dois eixos
do plano, centro e raio mínimo/máximo a partir do centro (raio igual = círculo).
"""
import argparse
from collections import defaultdict

import numpy as np

EIXOS = {"x": (0, (1, 2)), "y": (1, (0, 2)), "z": (2, (0, 1))}


def ler(caminho):
    d = np.fromfile(caminho, dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")], offset=84)
    return d["v"].astype(float)


def segmentos(tri, eixo, valor):
    i, (u, v) = EIXOS[eixo]
    d = tri[:, :, i] - valor
    cruza = ~((d > 0).all(1) | (d < 0).all(1))
    segs = []
    for t, dz in zip(tri[cruza], d[cruza]):
        pts = []
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]
            if (dz[k] > 0) != (dz[(k + 1) % 3] > 0):
                s = dz[k] / (dz[k] - dz[(k + 1) % 3])
                p = a + s * (b - a)
                pts.append((p[u], p[v]))
        if len(pts) == 2:
            segs.append(pts)
    return np.array(segs)


def contornos(segs):
    chave = lambda p: (round(p[0], 3), round(p[1], 3))
    vizinhos = defaultdict(list)
    for n, (a, b) in enumerate(segs):
        vizinhos[chave(a)].append(n)
        vizinhos[chave(b)].append(n)
    usado = np.zeros(len(segs), bool)
    grupos = []
    for n in range(len(segs)):
        if usado[n]:
            continue
        pilha, idx = [n], []
        while pilha:
            k = pilha.pop()
            if usado[k]:
                continue
            usado[k] = True
            idx.append(k)
            for p in segs[k]:
                pilha += [j for j in vizinhos[chave(p)] if not usado[j]]
        grupos.append(segs[idx].reshape(-1, 2))
    return sorted(grupos, key=lambda P: -np.ptp(P[:, 0]) * np.ptp(P[:, 1]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("stl")
    ap.add_argument("valores", nargs="+", type=float)
    ap.add_argument("--eixo", default="z", choices=EIXOS)
    ap.add_argument("--max", type=int, default=12, help="contornos listados por corte")
    ap.add_argument("--png", help="desenha os cortes empilhados nesta imagem")
    ap.add_argument("--escala", type=float, default=4.0, help="pixels por mm no PNG")
    a = ap.parse_args()
    tri = ler(a.stl)
    desenhos = []
    for valor in a.valores:
        segs = segmentos(tri, a.eixo, valor)
        grupos = contornos(segs) if len(segs) else []
        print(f"{a.eixo}={valor}: {len(grupos)} contornos")
        for P in grupos[:a.max]:
            c = (P.max(0) + P.min(0)) / 2
            e = P.max(0) - P.min(0)
            r = np.linalg.norm(P - c, axis=1)
            print(f"   {e[0]:8.2f} x {e[1]:8.2f}  centro ({c[0]:8.2f}, {c[1]:8.2f})  raio {r.min():7.2f}/{r.max():7.2f}")
        desenhos.append((valor, segs))
    if a.png:
        from PIL import Image, ImageDraw
        todos = np.concatenate([s.reshape(-1, 2) for _, s in desenhos if len(s)])
        mn, mx = todos.min(0) - 5, todos.max(0) + 5
        k = a.escala
        w, h = int((mx[0] - mn[0]) * k), int((mx[1] - mn[1]) * k)
        img = Image.new("RGB", (w, h * len(desenhos)), "white")
        d = ImageDraw.Draw(img)
        for n, (valor, segs) in enumerate(desenhos):
            oy = n * h
            d.text((5, oy + 5), f"{a.eixo}={valor}", fill="black")
            d.line([(0, oy), (w, oy)], fill=(200, 200, 200))
            for p, q in segs:
                d.line([((p[0] - mn[0]) * k, oy + h - (p[1] - mn[1]) * k),
                        ((q[0] - mn[0]) * k, oy + h - (q[1] - mn[1]) * k)], fill="black", width=2)
        img.save(a.png)
        print("PNG:", a.png)


if __name__ == "__main__":
    main()
