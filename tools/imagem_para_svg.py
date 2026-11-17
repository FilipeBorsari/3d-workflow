#!/usr/bin/env python3
"""Converte imagem (logo, silhueta, texto) em SVG vetorial para relevo 3D.

Usa `potrace` se instalado (melhor qualidade: sudo apt install potrace).
Sem potrace, usa um traçador próprio (contorno por pixel + simplificação + suavização).

Uso:
    python3 tools/imagem_para_svg.py logo.jpeg -o logo.svg
    python3 tools/imagem_para_svg.py logo.png -o logo.svg --limiar 100 --inverter
    python3 tools/imagem_para_svg.py logo.png -o logo.svg --previa previa.png  # confere a binarização

Por padrão, pixels escuros viram geometria. Use --inverter para logo claro em fundo escuro.
Depende de Pillow e numpy no Python do sistema.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

DIRECOES = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}


def binarizar(caminho, limiar, inverter, lado_min, desfoque):
    img = Image.open(caminho).convert("L")
    if max(img.size) < lado_min:
        escala = lado_min / max(img.size)
        img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    if desfoque:
        img = img.filter(ImageFilter.GaussianBlur(desfoque))
    pixels = np.asarray(img)
    mascara = pixels < limiar
    if inverter:
        mascara = ~mascara
    return limpar_mascara(mascara)


def limpar_mascara(mascara):
    """Remove ruído e pixels que só se tocam na diagonal.

    Contornos que se tocam num único ponto viram faces sobrepostas depois de
    suavizados, e a booleana do Blender gera arestas não-manifold.
    """
    img = Image.fromarray(mascara.astype(np.uint8) * 255)
    img = img.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))  # fecha frestas de 1-2 px
    img = img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))  # remove pontos soltos
    m = np.asarray(img) > 127
    for _ in range(20):
        a, b, c, d = m[:-1, :-1], m[:-1, 1:], m[1:, :-1], m[1:, 1:]
        diag1 = a & d & ~b & ~c
        diag2 = b & c & ~a & ~d
        if not (diag1.any() or diag2.any()):
            break
        m = m.copy()
        m[:-1, 1:] |= diag1  # liga o par diagonal preenchendo um vizinho
        m[:-1, :-1] |= diag2
    return m


def arestas_de_borda(mascara):
    """Arestas orientadas entre pixel cheio e vazio (cheio sempre à esquerda; y para baixo)."""
    m = np.pad(mascara, 1)
    cheio = m[1:-1, 1:-1]
    arestas = {}

    def adicionar(ys, xs, inicio, fim):
        for y, x in zip(ys.tolist(), xs.tolist()):
            a = (x + inicio[0], y + inicio[1])
            b = (x + fim[0], y + fim[1])
            arestas.setdefault(a, []).append(b)

    adicionar(*np.nonzero(cheio & ~m[:-2, 1:-1]), (1, 0), (0, 0))   # topo: direita -> esquerda
    adicionar(*np.nonzero(cheio & ~m[2:, 1:-1]), (0, 1), (1, 1))    # base: esquerda -> direita
    adicionar(*np.nonzero(cheio & ~m[1:-1, :-2]), (0, 0), (0, 1))   # esquerda: cima -> baixo
    adicionar(*np.nonzero(cheio & ~m[1:-1, 2:]), (1, 1), (1, 0))    # direita: baixo -> cima
    return arestas


def tracar_lacos(arestas):
    lacos = []
    while arestas:
        inicio = next(iter(arestas))
        laco = [inicio]
        atual, direcao = inicio, None
        while True:
            opcoes = arestas.get(atual)
            if not opcoes:
                break
            if len(opcoes) > 1 and direcao is not None:
                # Vértice ambíguo (pixels encostados na diagonal): escolha consistente,
                # sempre virar à direita (y para baixo: leste -> sul).
                preferida = (direcao + 1) % 4
                opcoes.sort(key=lambda p: (DIRECOES[(p[0] - atual[0], p[1] - atual[1])] - preferida) % 4)
            proximo = opcoes.pop(0)
            if not opcoes:
                del arestas[atual]
            direcao = DIRECOES[(proximo[0] - atual[0], proximo[1] - atual[1])]
            atual = proximo
            if atual == inicio:
                break
            laco.append(atual)
        if len(laco) >= 4:
            lacos.append(np.array(laco, dtype=float))
    return lacos


def douglas_peucker(pontos, tolerancia):
    if len(pontos) < 3:
        return pontos
    inicio, fim = pontos[0], pontos[-1]
    vetor = fim - inicio
    norma = np.hypot(*vetor)
    if norma == 0:
        distancias = np.hypot(*(pontos - inicio).T)
    else:
        distancias = np.abs(np.cross(vetor, pontos - inicio)) / norma
    indice = int(np.argmax(distancias))
    if distancias[indice] <= tolerancia:
        return np.array([inicio, fim])
    esquerda = douglas_peucker(pontos[:indice + 1], tolerancia)
    direita = douglas_peucker(pontos[indice:], tolerancia)
    return np.vstack([esquerda[:-1], direita])


def simplificar_fechado(laco, tolerancia):
    longe = int(np.argmax(np.hypot(*(laco - laco[0]).T)))
    metade1 = douglas_peucker(np.vstack([laco[:longe + 1]]), tolerancia)
    metade2 = douglas_peucker(np.vstack([laco[longe:], laco[:1]]), tolerancia)
    return np.vstack([metade1[:-1], metade2[:-1]])


def chaikin(laco, iteracoes):
    """Suaviza um polígono fechado cortando cada canto (Chaikin)."""
    for _ in range(iteracoes):
        seguinte = np.roll(laco, -1, axis=0)
        novo = np.empty((len(laco) * 2, 2))
        novo[0::2] = 0.75 * laco + 0.25 * seguinte
        novo[1::2] = 0.25 * laco + 0.75 * seguinte
        laco = novo
    return laco


def tracar_interno(mascara, tolerancia, suavizar, area_min):
    caminhos = []
    for laco in tracar_lacos(arestas_de_borda(mascara)):
        x, y = laco.T
        area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        if area < area_min:
            continue
        pontos = simplificar_fechado(laco, tolerancia)
        if len(pontos) < 3:
            continue
        pontos = chaikin(pontos, suavizar)
        caminhos.append("M " + " L ".join(f"{px:.2f} {py:.2f}" for px, py in pontos) + " Z")
    altura, largura = mascara.shape
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" '
            f'viewBox="0 0 {largura} {altura}">\n'
            f'<path fill="#000" fill-rule="evenodd" d="{" ".join(caminhos)}"/>\n</svg>\n'), len(caminhos)


def tracar_potrace(mascara, destino):
    with tempfile.TemporaryDirectory() as tmp:
        pbm = Path(tmp) / "entrada.pbm"
        Image.fromarray(mascara.astype(np.uint8) * 255).convert("1").save(pbm)
        # PBM: 1 = preto. Pillow grava branco=1, então invertemos com --invert.
        subprocess.run(["potrace", str(pbm), "--svg", "--invert", "-o", str(destino)], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("imagem")
    p.add_argument("-o", "--saida", required=True)
    p.add_argument("--limiar", type=int, default=128, help="0-255; pixels abaixo viram geometria")
    p.add_argument("--inverter", action="store_true", help="pixels claros viram geometria")
    p.add_argument("--lado-min", type=int, default=1500, help="amplia imagens pequenas antes de traçar")
    p.add_argument("--desfoque", type=float, default=1.0, help="desfoque antes do limiar (remove serrilhado)")
    p.add_argument("--tolerancia", type=float, default=1.0, help="simplificação em pixels")
    p.add_argument("--suavizar", type=int, default=2, help="iterações de suavização (0 = cantos vivos)")
    p.add_argument("--area-min", type=float, default=40, help="descarta manchas menores (px²)")
    p.add_argument("--previa", help="salva PNG da binarização para conferência")
    p.add_argument("--sem-potrace", action="store_true")
    args = p.parse_args()

    mascara = binarizar(args.imagem, args.limiar, args.inverter, args.lado_min, args.desfoque)
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if args.previa:
        Path(args.previa).parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray((~mascara).astype(np.uint8) * 255).save(args.previa)

    if shutil.which("potrace") and not args.sem_potrace:
        tracar_potrace(mascara, destino)
        print(f"SVG (potrace): {destino}")
    else:
        svg, n = tracar_interno(mascara, args.tolerancia, args.suavizar, args.area_min)
        destino.write_text(svg)
        print(f"SVG (traçador interno, {n} contornos): {destino}")
    print(f"pixels de geometria: {mascara.mean():.1%} da imagem {mascara.shape[1]}x{mascara.shape[0]}")


if __name__ == "__main__":
    sys.exit(main())
