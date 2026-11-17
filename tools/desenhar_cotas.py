"""Desenha cotas sobre as vistas renderizadas por bl/cotas.py e monta a folha (Pillow).

Uso: python3 tools/desenhar_cotas.py pasta/cotas.json
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTE_NEGRITO = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COR = (200, 30, 30)
COR_NOTA = (20, 70, 160)


def px(vista, p):
    i, j = vista["eixos"]
    k, r = vista["px_mm"], vista["resolucao"]
    cu, cv = vista["centro"]
    return (r / 2 + (p[i] - cu) * k, r / 2 - (p[j] - cv) * k)


def seta(d, ponta, direcao, tam=14):
    ang = math.atan2(direcao[1], direcao[0])
    a1, a2 = ang + math.radians(160), ang - math.radians(160)
    d.polygon([ponta, (ponta[0] + tam * math.cos(a1), ponta[1] + tam * math.sin(a1)),
               (ponta[0] + tam * math.cos(a2), ponta[1] + tam * math.sin(a2))], fill=COR)


def texto_caixa(d, centro, texto, fonte, cor):
    x0, y0, x1, y1 = d.textbbox((0, 0), texto, font=fonte)
    w, h = x1 - x0, y1 - y0
    caixa = (centro[0] - w / 2 - 5, centro[1] - h / 2 - 5, centro[0] + w / 2 + 5, centro[1] + h / 2 + 5)
    d.rectangle(caixa, fill=(255, 255, 255), outline=cor, width=2)
    d.text((centro[0] - w / 2 - x0, centro[1] - h / 2 - y0), texto, font=fonte, fill=cor)


def desenhar_vista(vista, fonte):
    img = Image.open(vista["arquivo"]).convert("RGB")
    d = ImageDraw.Draw(img)
    for c in vista["cotas"]:
        if c["tipo"] == "linha":
            a, b = px(vista, c["a"]), px(vista, c["b"])
            dx, dy = b[0] - a[0], b[1] - a[1]
            comp = math.hypot(dx, dy) or 1
            ux, uy = dx / comp, dy / comp
            nx, ny = -uy * c["lado"], ux * c["lado"]
            off = c["dist"] * vista["px_mm"]
            a2 = (a[0] + nx * off, a[1] + ny * off)
            b2 = (b[0] + nx * off, b[1] + ny * off)
            for p, q in ((a, a2), (b, b2)):       # linhas de chamada
                d.line([(p[0] + nx * 4, p[1] + ny * 4), (q[0] + nx * 8, q[1] + ny * 8)], fill=COR, width=2)
            d.line([a2, b2], fill=COR, width=3)
            seta(d, a2, (-ux, -uy))
            seta(d, b2, (ux, uy))
            texto_caixa(d, ((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2), c["texto"], fonte, COR)
        else:
            p = px(vista, c["p"])
            q = (p[0] + c["dx"] * vista["px_mm"], p[1] - c["dy"] * vista["px_mm"])
            d.line([p, q], fill=COR_NOTA, width=2)
            d.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), fill=COR_NOTA)
            texto_caixa(d, q, c["texto"], fonte, COR_NOTA)
    return img


def main(caminho):
    dados = json.loads(Path(caminho).read_text())
    fonte = ImageFont.truetype(FONTE, 26)
    titulo_f = ImageFont.truetype(FONTE_NEGRITO, 40)
    sub_f = ImageFont.truetype(FONTE_NEGRITO, 30)
    paineis = []
    for v in dados["vistas"]:
        img = desenhar_vista(v, fonte)
        d = ImageDraw.Draw(img)
        d.text((20, 15), v["titulo"], font=sub_f, fill=(0, 0, 0))
        paineis.append(img)
    lado = paineis[0].size[0]
    colunas = 2
    linhas = math.ceil(len(paineis) / colunas)
    topo, rodape = 90, 50 + 36 * len(dados["notas"])
    folha = Image.new("RGB", (colunas * lado, topo + linhas * lado + rodape), "white")
    d = ImageDraw.Draw(folha)
    d.text((20, 20), dados["titulo"], font=titulo_f, fill=(0, 0, 0))
    for n, img in enumerate(paineis):
        x, y = (n % colunas) * lado, topo + (n // colunas) * lado
        folha.paste(img, (x, y))
        d.rectangle((x, y, x + lado - 1, y + lado - 1), outline=(180, 180, 180), width=2)
    y = topo + linhas * lado + 20
    for n in dados["notas"]:
        d.text((20, y), n, font=fonte, fill=(0, 0, 0))
        y += 36
    folha.save(dados["saida"])
    print("COTAS:", dados["saida"])


if __name__ == "__main__":
    main(sys.argv[1])
