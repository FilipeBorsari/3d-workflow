"""Contornos 2D fechados (retângulo arredondado, estádio) e sólidos feitos de anéis empilhados.

Serve para potes, lixeiras e cestos com planta arredondada e estrias verticais, sem booleana:
cada anel é o contorno deslocado na normal (parede, folga, estria) numa altura z, e
`solido` liga anéis consecutivos com quads e fecha o primeiro e o último com n-gonos.

    c = contorno.Contorno(100, 140, 50)            # estádio 100 x 140 (raio = metade da largura)
    a = c.amostrar(0.2)                            # pontos a cada ~0,2 mm de perímetro
    d = contorno.estrias(a, passo=6.2, largura_sulco=2.2, fundo=2.4)
    copo = contorno.solido([
        a.anel(0, -1), a.anel(1),                  # chanfro de 1 mm na base
        a.anel(3), a.anel(5.4, d), ...,            # estrias com rampa de 45° nas pontas
        a.anel(150), a.anel(150, -4),              # borda
        a.anel(3, -4),                             # fundo interno (último anel, tampa para cima)
    ], "copo")

Todos os anéis de um sólido vêm da mesma amostra (mesmo número de pontos). A ordem dos
anéis percorre a seção de fora para dentro, como o perfil de `formas.revolucao`.
"""
import math

import bmesh
import bpy
import numpy as np


class Contorno:
    """Retângulo arredondado centrado na origem: largura em X, comprimento em Y.

    raio = min(largura, comprimento) / 2 vira estádio (pontas semicirculares).
    raio_y diferente de raio deixa os cantos elípticos (semieixos raio em X e raio_y em Y):
    é o estádio de um original escalado com fatores diferentes em X e Y.
    O percurso começa no meio do lado da frente (-Y) e segue no sentido anti-horário.
    """

    def __init__(self, largura, comprimento, raio, raio_y=None):
        self.largura, self.comprimento = largura, comprimento
        self.raio = min(raio, largura / 2, comprimento / 2)
        self.raio_y = min(raio_y, comprimento / 2) if raio_y else self.raio
        rx, ry = self.raio, self.raio_y
        a, b = largura / 2 - rx, comprimento / 2 - ry
        # trechos: ("linha", inicio, fim, normal) ou ("arco", centro, ang_inicio, ang_fim)
        self.trechos = [
            ("linha", (0, -b - ry), (a, -b - ry), (0, -1)),
            ("arco", (a, -b), -90, 0),
            ("linha", (a + rx, -b), (a + rx, b), (1, 0)),
            ("arco", (a, b), 0, 90),
            ("linha", (a, b + ry), (-a, b + ry), (0, 1)),
            ("arco", (-a, b), 90, 180),
            ("linha", (-a - rx, b), (-a - rx, -b), (-1, 0)),
            ("arco", (-a, -b), 180, 270),
            ("linha", (-a, -b - ry), (0, -b - ry), (0, -1)),
        ]
        self._tabelas = {}
        self.comprimentos = [self._comprimento(i, t) for i, t in enumerate(self.trechos)]
        self.perimetro = sum(self.comprimentos)

    def _comprimento(self, i, t):
        if t[0] == "linha":
            return math.dist(t[1], t[2])
        if self.raio == self.raio_y:
            return math.radians(t[3] - t[2]) * self.raio
        # arco de elipse: tabela ângulo x comprimento acumulado, invertida em ponto()
        ang = np.radians(np.linspace(t[2], t[3], 4001))
        xy = np.column_stack([self.raio * np.cos(ang), self.raio_y * np.sin(ang)])
        acum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
        self._tabelas[i] = (acum, ang)
        return float(acum[-1])

    def ponto(self, s):
        """Ponto e normal para fora no comprimento de arco s (mm)."""
        s = s % self.perimetro
        for i, (t, comp) in enumerate(zip(self.trechos, self.comprimentos)):
            if s <= comp or t is self.trechos[-1]:
                f = s / comp if comp else 0.0
                if t[0] == "linha":
                    p = (t[1][0] + f * (t[2][0] - t[1][0]), t[1][1] + f * (t[2][1] - t[1][1]))
                    return p, t[3]
                if i in self._tabelas:
                    acum, angs = self._tabelas[i]
                    ang = float(np.interp(s, acum, angs))
                else:
                    ang = math.radians(t[2] + f * (t[3] - t[2]))
                c, sn = math.cos(ang), math.sin(ang)
                n = (c / self.raio, sn / self.raio_y)
                tam = math.hypot(*n)
                return (t[1][0] + self.raio * c, t[1][1] + self.raio_y * sn), (n[0] / tam, n[1] / tam)
            s -= comp

    def amostrar(self, passo, fase=0.0):
        """Amostra uniforme do perímetro com passo ~`passo` mm, a partir de s = fase."""
        n = max(8, round(self.perimetro / passo))
        s = fase + np.arange(n) * self.perimetro / n
        pts, nrm = zip(*(self.ponto(x) for x in s))
        return Amostra(self, s, np.array(pts), np.array(nrm))


class Amostra:
    """Pontos de um contorno (mesma contagem em todos os anéis de um sólido)."""

    def __init__(self, contorno, s, pontos, normais):
        self.contorno, self.s, self.pontos, self.normais = contorno, s, pontos, normais

    def __len__(self):
        return len(self.s)

    def anel(self, z, deslocamento=0.0):
        """Anel (N, 3) na altura z (escalar ou array por ponto), deslocado na normal.

        deslocamento: mm para fora (> 0) ou para dentro (< 0), escalar ou array por ponto.
        """
        d = np.broadcast_to(np.asarray(deslocamento, float), (len(self),))
        xy = self.pontos + self.normais * d[:, None]
        zz = np.broadcast_to(np.asarray(z, float), (len(self),))
        return np.column_stack([xy, zz])


def estrias(amostra, passo, largura_sulco, fundo, forma="reta", rampa=None):
    """Deslocamento (<= 0) de cada ponto para cavar sulcos verticais no contorno.

    O número de sulcos é inteiro: o passo real é perímetro / round(perímetro / passo).
    forma "reta": sulco de fundo plano com paredes de largura `rampa` (padrão: 1 amostra).
    forma "concava": sulco em arco de círculo (canelura), largura e fundo dados.
    """
    perimetro = amostra.contorno.perimetro
    n = max(1, round(perimetro / passo))
    passo = perimetro / n
    x = np.mod(amostra.s, passo)
    dist = np.abs(x - passo / 2)
    meia = largura_sulco / 2
    if forma == "reta":
        rampa = rampa or perimetro / len(amostra)
        f = np.clip((meia + rampa / 2 - dist) / rampa, 0, 1)
    else:
        raio = (meia ** 2 + fundo ** 2) / (2 * fundo)
        f = np.clip((np.sqrt(np.clip(raio ** 2 - dist ** 2, 0, None)) - (raio - fundo)) / fundo, 0, 1)
    return -fundo * f


def solido(aneis, nome="solido", ciclo=False):
    """Liga anéis consecutivos com quads e fecha o primeiro e o último com n-gonos.

    ciclo=True liga o último anel ao primeiro em vez de fechar com n-gonos (anel, aro, tubo).
    """
    bm = bmesh.new()
    camadas = [[bm.verts.new(tuple(p)) for p in anel] for anel in aneis]
    n = len(camadas[0])
    pares = list(zip(camadas, camadas[1:])) + ([(camadas[-1], camadas[0])] if ciclo else [])
    for baixo, cima in pares:
        for j in range(n):
            k = (j + 1) % n
            bm.faces.new((baixo[j], baixo[k], cima[k], cima[j]))
    if not ciclo:
        bm.faces.new(list(reversed(camadas[0])))
        bm.faces.new(camadas[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj
