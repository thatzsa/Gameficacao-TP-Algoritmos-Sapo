# Sapo no Rio - jogo em pygame
#
# Usa a mesma logica do trabalho de algoritmos: BFS em estados
# (pedra atual, saltos longos seguidos). O jogo usa a BFS pra:
#   1) garantir que todo rio gerado tem solucao
#   2) mostrar a solucao otima no final e comparar com a do jogador
#
# Como jogar: clique numa pedra, depois escolha "Curto" ou "Longo".
#   - curto: ate X de distancia (zera o cansaco)
#   - longo: ate Y de distancia, mas so K seguidos
# R recomeca o rio, Esc fecha.
#
# Precisa de: pip install pygame
# E da foto "sapo_parabens.png" na mesma pasta deste arquivo.

import math
import os
import random
from collections import deque

import pygame

LARGURA, ALTURA = 1000, 640
FPS = 60

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_FOTO = os.path.join(PASTA, "sapo_parabens.png")

# layout da cena
HORIZONTE = 300
AGUA_TOPO = 312
XL, XR = 130, 870       # centro das rochas das margens
Y_PEDRA = 484           # altura (centro) das pedras no rio

# cores
BRANCO = (255, 255, 255)
PRETO = (20, 20, 20)
CREME = (255, 243, 214)
MARROM_ESC = (96, 58, 28)
VERDE_ESC = (24, 118, 44)
VERDE = (42, 150, 56)
VERDE_CLARO = (96, 200, 90)
LARANJA = (240, 130, 30)
ROXO = (150, 60, 200)
AREIA = (222, 170, 108)


# ------------------------------------------------------------------
# logica do problema (a mesma do trabalho)
# ------------------------------------------------------------------

def movimentos_bfs(pos, i, c, X, Y, K):
    """Pulos que a BFS precisa considerar a partir de (i, c).
    Se da pra ir de curto, curto sempre e melhor (zera o contador)."""
    for j in range(i + 1, len(pos)):
        d = pos[j] - pos[i]
        if d > Y:
            break  # pedras ordenadas: as proximas so ficam mais longe
        if d <= X:
            yield j, 0, "curto"
        elif c < K:
            yield j, c + 1, "longo"


def bfs(pos, X, Y, K):
    """Devolve a lista de pulos (i, j, tipo) do menor caminho, ou None."""
    n = len(pos)
    pai = {(0, 0): None}
    fila = deque([(0, 0)])
    while fila:
        est = fila.popleft()
        if est[0] == n - 1:
            caminho = []
            while pai[est] is not None:
                ant, tipo = pai[est]
                caminho.append((ant[0], est[0], tipo))
                est = ant
            return caminho[::-1]
        for j, novo_c, tipo in movimentos_bfs(pos, est[0], est[1], X, Y, K):
            if (j, novo_c) not in pai:
                pai[(j, novo_c)] = (est, tipo)
                fila.append((j, novo_c))
    return None


class Rio:
    def __init__(self, pos, X, Y, K, caminho):
        self.pos = pos
        self.X, self.Y, self.K = X, Y, K
        self.caminho = caminho
        self.otimo = len(caminho)
        self.n = len(pos)
        self.unidade = (XR - XL) / (pos[-1] - 1)

    def x(self, i):
        return XL + (self.pos[i] - 1) * self.unidade

    def margem(self, i):
        return i == 0 or i == self.n - 1

    def largura(self, i):
        if self.margem(i):
            return 120
        return max(18, min(42, self.unidade * 0.85))

    def topo(self, i):
        """y onde o sapo pisa."""
        return 452 if self.margem(i) else Y_PEDRA - 10


def parametros_nivel(nivel):
    M = min(18 + 2 * nivel, 30)
    n_pedras = min(4 + nivel, 10)
    X = random.choice([3, 4])
    Y = X + random.choice([3, 4, 5])
    K = 3 if nivel <= 2 else (2 if nivel <= 5 else 1)
    return M, n_pedras, X, Y, K


def gerar_rio(nivel):
    """Sorteia rios ate achar um com solucao em que os saltos longos
    realmente fazem diferenca (so com curtos seria pior ou impossivel)."""
    minimo = 3 + nivel // 3
    for tentativa in range(4000):
        M, n_pedras, X, Y, K = parametros_nivel(nivel)
        pedras = sorted(random.sample(range(2, M), n_pedras))
        pos = [1] + pedras + [M]
        caminho = bfs(pos, X, Y, K)
        if caminho is None:
            continue
        if tentativa < 3000:
            if len(caminho) < minimo:
                continue
            so_curto = bfs(pos, X, Y, 0)
            if so_curto is not None and len(so_curto) <= len(caminho):
                continue
        return Rio(pos, X, Y, K, caminho)
    # nunca deve chegar aqui, mas por garantia
    return Rio([1, 5, 9, 13], 4, 8, 2, bfs([1, 5, 9, 13], 4, 8, 2))


# ------------------------------------------------------------------
# helpers de desenho
# ------------------------------------------------------------------

def lerp(a, b, u):
    return a + (b - a) * u


def cor_lerp(c1, c2, u):
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), max(1, int(w)), max(1, int(h)))


def borda_esq(y):
    # margem esquerda do rio: ele vai afinando la no fundo
    return 95 + 255 * ((ALTURA - y) / (ALTURA - AGUA_TOPO)) ** 1.6


def borda_dir(y):
    return LARGURA - borda_esq(y)


def elipse_alpha(tela, cor, rect, largura=0):
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, cor, s.get_rect(), largura)
    tela.blit(s, rect.topleft)


def texto(tela, fonte, msg, cor, pos, ancora="topleft", sombra=None, contorno=None):
    img = fonte.render(msg, True, cor)
    r = img.get_rect(**{ancora: pos})
    if contorno:
        borda = fonte.render(msg, True, contorno)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            tela.blit(borda, r.move(dx, dy))
    elif sombra:
        tela.blit(fonte.render(msg, True, sombra), r.move(2, 2))
    tela.blit(img, r)
    return r


def painel(tela, rect, cor=(156, 104, 56)):
    pygame.draw.rect(tela, MARROM_ESC, rect.inflate(8, 8), border_radius=18)
    pygame.draw.rect(tela, cor, rect, border_radius=14)
    for k in (1, 2):
        y = rect.y + rect.h * k / 3
        pygame.draw.line(tela, (128, 82, 42), (rect.x + 10, y), (rect.right - 10, y), 2)


class Botao:
    def __init__(self, rect, rotulo):
        self.rect = rect
        self.rotulo = rotulo
        self.ativo = True

    def desenhar(self, tela, fonte, mouse):
        if not self.ativo:
            cor, cor_txt = (150, 136, 118), (205, 195, 180)
        elif self.rect.collidepoint(mouse):
            cor, cor_txt = (224, 176, 112), (70, 40, 15)
        else:
            cor, cor_txt = (200, 152, 92), (70, 40, 15)
        pygame.draw.rect(tela, MARROM_ESC, self.rect.inflate(6, 6), border_radius=12)
        pygame.draw.rect(tela, cor, self.rect, border_radius=10)
        pygame.draw.line(tela, cor_lerp(cor, BRANCO, 0.35),
                         (self.rect.x + 10, self.rect.y + 4), (self.rect.right - 10, self.rect.y + 4), 2)
        texto(tela, fonte, self.rotulo, cor_txt, self.rect.center, "center")

    def clicado(self, pos):
        return self.ativo and self.rect.collidepoint(pos)


# ------------------------------------------------------------------
# cenario
# ------------------------------------------------------------------

def desenhar_junco(sup, x, y):
    for k in range(6):
        dx = (k - 3) * 4
        lean = (k - 2.5) * 3
        h = 26 + (k * 7) % 14
        cor = (58, 140, 52) if k % 2 == 0 else (38, 108, 42)
        pygame.draw.polygon(sup, cor, [(x + dx, y), (x + dx + 4, y), (x + dx + lean + 2, y - h)])


def desenhar_flor(sup, x, y, r, petala, miolo):
    pygame.draw.line(sup, (50, 130, 50), (x, y), (x, y + r * 3), 3)
    for k in range(6):
        ang = k * math.tau / 6
        pygame.draw.circle(sup, petala, (int(x + math.cos(ang) * r), int(y + math.sin(ang) * r)), int(r * 0.7))
    pygame.draw.circle(sup, miolo, (int(x), int(y)), int(r * 0.55))


def montar_fundo():
    ceu = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        pygame.draw.line(ceu, cor_lerp((50, 150, 235), (178, 226, 252), min(1, y / 340)), (0, y), (LARGURA, y))

    chao = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    # morros ao fundo (cx, raio x, raio y, cor)
    base = HORIZONTE + 12
    morros = [
        (90, 270, 78, (44, 140, 60)),
        (380, 230, 60, (62, 162, 64)),
        (740, 190, 92, (205, 122, 56)),     # o morro marrom da ilustracao
        (900, 280, 86, (50, 148, 58)),
        (620, 230, 56, (46, 142, 60)),
    ]
    for cx, rx, ry, cor in morros:
        pygame.draw.ellipse(chao, cor, R(cx - rx, base - ry, 2 * rx, 2 * ry))
    pygame.draw.ellipse(chao, (226, 150, 78), R(690, base - 82, 120, 46))   # brilho do morro marrom

    # campo (gradiente)
    for y in range(base, ALTURA):
        u = (y - base) / (ALTURA - base)
        pygame.draw.line(chao, cor_lerp((166, 218, 72), (104, 182, 46), u), (0, y), (LARGURA, y))

    # agua
    for y in range(AGUA_TOPO, ALTURA):
        u = (y - AGUA_TOPO) / (ALTURA - AGUA_TOPO)
        pygame.draw.line(chao, cor_lerp((140, 204, 250), (28, 116, 222), u ** 0.8),
                         (borda_esq(y), y), (borda_dir(y), y))

    # barranco de areia
    esq = [(borda_esq(y), y) for y in range(AGUA_TOPO, ALTURA, 4)]
    dire = [(borda_dir(y), y) for y in range(AGUA_TOPO, ALTURA, 4)]
    pygame.draw.lines(chao, AREIA, False, esq, 8)
    pygame.draw.lines(chao, AREIA, False, dire, 8)

    # morrinhos que escondem a nascente do rio
    pygame.draw.ellipse(chao, (58, 160, 62), R(320, AGUA_TOPO - 36, 360, 62))
    pygame.draw.ellipse(chao, (76, 178, 68), R(380, AGUA_TOPO - 28, 240, 46))

    # ponte la no fundo (quebrada, claro)
    yp = 346
    xa, xb = borda_esq(yp) - 8, borda_dir(yp) + 8
    k = 0
    x = xa
    while x < xb:
        if k not in (7, 8):
            pygame.draw.polygon(chao, (176, 128, 74), [(x, yp), (x + 28, yp), (x + 24, yp + 13), (x - 4, yp + 13)])
            pygame.draw.polygon(chao, (214, 168, 108), [(x, yp), (x + 28, yp), (x + 27, yp + 4), (x - 1, yp + 4)])
        x += 31
        k += 1
    pygame.draw.line(chao, (110, 70, 34), (xa, yp - 14), (xa, yp + 14), 5)
    pygame.draw.line(chao, (110, 70, 34), (xb, yp - 14), (xb, yp + 14), 5)

    # arvore da esquerda
    pygame.draw.lines(chao, (84, 58, 32), False, [(52, 440), (58, 404), (46, 376)], 9)
    pygame.draw.line(chao, (84, 58, 32), (57, 404), (92, 388), 6)
    for (ex, ey, ew, eh) in [(10, 350, 74, 34), (66, 366, 66, 30), (30, 336, 52, 26)]:
        pygame.draw.ellipse(chao, (52, 150, 52), R(ex, ey, ew, eh))
        pygame.draw.ellipse(chao, (86, 184, 70), R(ex + 6, ey + 3, ew * 0.6, eh * 0.45))

    # junco nas margens
    for (jx, jy) in [(158, 548), (150, 566), (842, 548), (850, 566), (170, 514), (830, 514)]:
        desenhar_junco(chao, jx, jy)

    # flores (cantinho direito, igual a ilustracao)
    desenhar_flor(chao, 950, 538, 12, (240, 124, 200), (255, 220, 70))
    desenhar_flor(chao, 922, 512, 9, (255, 255, 255), (255, 210, 60))
    desenhar_flor(chao, 60, 560, 8, (255, 255, 255), (255, 210, 60))
    for (gx, gy) in [(30, 480), (210, 600), (790, 600), (980, 600), (20, 610)]:
        desenhar_junco(chao, gx, gy)

    return ceu, chao


def desenhar_sol(tela, t):
    cx, cy = 880, 92
    for k in range(12):
        ang = t * 0.25 + k * math.tau / 12
        r1, r2 = 58, 80 + 5 * math.sin(t * 2 + k)
        p0 = (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)
        p1 = (cx + math.cos(ang) * r2, cy + math.sin(ang) * r2)
        pygame.draw.line(tela, (255, 206, 56), p0, p1, 7)
        pygame.draw.circle(tela, (255, 206, 56), (int(p1[0]), int(p1[1])), 3)
    pygame.draw.circle(tela, (255, 198, 48), (cx, cy), 50)
    pygame.draw.circle(tela, (255, 224, 100), (cx, cy), 41)
    pygame.draw.circle(tela, (255, 242, 170), (cx - 8, cy - 9), 20)


def desenhar_nuvem(tela, x, y, s):
    blobs = [(0, 0, 26), (28, -10, 32), (62, -2, 28), (90, 6, 20), (-24, 8, 18)]
    for dx, dy, r in blobs:
        pygame.draw.circle(tela, (196, 228, 250), (int(x + dx * s), int(y + dy * s)), int(r * s + 3))
    for dx, dy, r in blobs:
        pygame.draw.circle(tela, BRANCO, (int(x + dx * s), int(y + dy * s)), int(r * s))


def desenhar_rocha(tela, cx, cy, w, h, musgo=False):
    pygame.draw.ellipse(tela, (70, 72, 80), R(cx - w / 2, cy - h / 2 + 6, w, h))
    pygame.draw.ellipse(tela, (128, 131, 140), R(cx - w / 2, cy - h / 2, w, h * 0.88))
    pygame.draw.ellipse(tela, (166, 169, 178), R(cx - w * 0.36, cy - h / 2 + 3, w * 0.5, h * 0.36))
    if musgo:
        pygame.draw.ellipse(tela, (92, 162, 66), R(cx + w * 0.08, cy - h / 2 + 3, w * 0.3, h * 0.2))
        pygame.draw.ellipse(tela, (92, 162, 66), R(cx - w * 0.44, cy - h / 2 + h * 0.3, w * 0.18, h * 0.16))


def desenhar_sapo(tela, cx, base, sx=1.0, sy=1.0, olhar=(1, 0), cansado=False, t=0.0, escala=1.0):
    s = escala
    w = 40 * s * sx
    h = 52 * s * sy
    x0 = cx - w / 2
    y0 = base - h
    # patinhas
    pygame.draw.ellipse(tela, VERDE_ESC, R(cx - w * 0.74, base - 11 * s * sy, w * 0.62, 12 * s * sy))
    pygame.draw.ellipse(tela, VERDE_ESC, R(cx + w * 0.12, base - 11 * s * sy, w * 0.62, 12 * s * sy))
    # corpo em formato de vasinho
    pygame.draw.ellipse(tela, VERDE_ESC, R(x0, y0, w, h))
    pygame.draw.ellipse(tela, VERDE, R(x0 + w * 0.06, y0 + h * 0.04, w * 0.88, h * 0.92))
    pygame.draw.ellipse(tela, VERDE_CLARO, R(x0 + w * 0.16, y0 + h * 0.16, w * 0.24, h * 0.40))
    pygame.draw.ellipse(tela, (156, 218, 112), R(cx - w * 0.22, base - h * 0.48, w * 0.44, h * 0.38))
    # bracinhos
    pygame.draw.ellipse(tela, VERDE_ESC, R(x0 - w * 0.10, base - h * 0.46, w * 0.24, h * 0.30))
    pygame.draw.ellipse(tela, VERDE_ESC, R(x0 + w * 0.86, base - h * 0.46, w * 0.24, h * 0.30))
    # olhos
    ey = y0 + h * 0.12
    er = 9 * s
    for lado in (-1, 1):
        ex = cx + lado * w * 0.25
        pygame.draw.circle(tela, VERDE_ESC, (int(ex), int(ey)), int(er + 2))
        pygame.draw.circle(tela, BRANCO, (int(ex), int(ey)), int(er))
        px = ex + olhar[0] * 3.2 * s
        py = ey + olhar[1] * 3.2 * s + (2 * s if cansado else 0)
        pygame.draw.circle(tela, PRETO, (int(px), int(py)), max(2, int(4.6 * s)))
        pygame.draw.circle(tela, BRANCO, (int(px - 1.5 * s), int(py - 1.8 * s)), max(1, int(1.6 * s)))
        if cansado:  # palpebra caida
            rr = er + 2
            pts = [(ex + rr * math.cos(a), ey - rr * math.sin(a)) for a in [k * math.pi / 12 for k in range(13)]]
            pygame.draw.polygon(tela, VERDE, pts)
            pygame.draw.line(tela, VERDE_ESC, (ex - rr, ey), (ex + rr, ey), 2)
    # boquinha
    boca = R(cx - w * 0.16, y0 + h * 0.30, w * 0.32, h * 0.14)
    if cansado:
        pygame.draw.arc(tela, VERDE_ESC, boca.move(0, 4), math.pi * 0.15, math.pi * 0.85, 2)
        gy = y0 + h * 0.05 + (t * 24) % 14
        pygame.draw.circle(tela, (120, 200, 255), (int(x0 + w + 6 * s), int(gy)), max(2, int(3 * s)))
    else:
        pygame.draw.arc(tela, VERDE_ESC, boca, math.pi * 1.1, math.pi * 1.9, 2)


def desenhar_arco(tela, x0, y0, x1, y1, altura, cor, espessura, tracejado, baixo=False):
    n = 30
    pts = []
    for k in range(n + 1):
        u = k / n
        sinal = 1 if baixo else -1
        pts.append((lerp(x0, x1, u), lerp(y0, y1, u) + sinal * 4 * altura * u * (1 - u)))
    if tracejado:
        for k in range(n):
            if (k // 2) % 2 == 0:
                pygame.draw.line(tela, cor, pts[k], pts[k + 1], espessura)
    else:
        pygame.draw.lines(tela, cor, False, pts, espessura)
    pygame.draw.circle(tela, cor, (int(x1), int(y1)), espessura + 1)
    return pts[n // 2]


# ------------------------------------------------------------------
# animacao de pulo
# ------------------------------------------------------------------

class Pulo:
    def __init__(self, rio, i, j, tipo):
        self.i, self.j, self.tipo = i, j, tipo
        self.dur = 0.55 if tipo == "curto" else 0.80
        dx = abs(rio.x(j) - rio.x(i))
        self.altura = 28 + 0.30 * dx + (24 if tipo == "longo" else 0)
        self.t = 0.0

    def terminou(self):
        return self.t >= self.dur

    def pose(self, rio):
        u = min(1.0, self.t / self.dur)
        x = lerp(rio.x(self.i), rio.x(self.j), u)
        y = lerp(rio.topo(self.i), rio.topo(self.j), u) - 4 * self.altura * u * (1 - u)
        # estica no ar, agacha na saida e na chegada
        sy = 1 + 0.18 * math.sin(math.pi * u)
        sx = 1 / sy
        agacha = max(0, 1 - u / 0.15) + max(0, (u - 0.85) / 0.15)
        sy -= 0.25 * agacha
        sx += 0.20 * agacha
        return x, y, sx, sy


# ------------------------------------------------------------------
# jogo
# ------------------------------------------------------------------

class Jogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Sapo no Rio")
        self.relogio = pygame.time.Clock()

        nomes = "trebuchetms,verdana,dejavusans,arial"
        self.f_peq = pygame.font.SysFont(nomes, 17, bold=True)
        self.f_med = pygame.font.SysFont(nomes, 24, bold=True)
        self.f_gra = pygame.font.SysFont(nomes, 38, bold=True)
        self.f_enorme = pygame.font.SysFont(nomes, 76, bold=True)

        self.ceu, self.chao = montar_fundo()
        self.polaroid = self.montar_polaroid()

        self.t = 0.0
        self.rodando = True
        self.nuvens = [[120, 70, 1.0, 9], [520, 120, 0.8, 6], [820, 190, 0.7, 5]]
        self.peixe = None
        self.prox_peixe = 3.0
        self.aneis = []       # ondas de pouso
        self.gotas = []       # respingos
        self.confete = []

        self.botao_curto = Botao(R(0, 0, 108, 38), "Pulo curto")
        self.botao_longo = Botao(R(0, 0, 108, 38), "Pulo longo")
        self.botao_ver = Botao(R(350, 580, 300, 46), "Ver a solução ótima")
        self.botao_repetir = Botao(R(232, 138, 250, 40), "Tentar este rio de novo")
        self.botao_prox = Botao(R(498, 138, 270, 40), "Próximo nível >>")

        self.nivel = 1
        self.novo_rio()

    # ---------- estado ----------
    def novo_rio(self):
        self.rio = gerar_rio(self.nivel)
        self.reiniciar()

    def reiniciar(self):
        self.atual = 0
        self.c = 0
        self.saltos = 0
        self.historico = []
        self.sel = None
        self.pulo = None
        self.encalhou = False
        self.estado = "jogando"
        self.replay = {"i": 0, "idx": 0, "pulo": None, "espera": 0.8}

    def montar_polaroid(self):
        try:
            img = pygame.image.load(ARQ_FOTO).convert_alpha()
            foto = pygame.transform.smoothscale(img, (300, 300))
        except (pygame.error, FileNotFoundError):
            foto = pygame.Surface((300, 300))
            foto.fill((150, 205, 120))
            desenhar_sapo(foto, 150, 250, escala=3.2)
        cartao = pygame.Surface((332, 376), pygame.SRCALPHA)
        pygame.draw.rect(cartao, (0, 0, 0, 70), R(6, 8, 326, 368), border_radius=8)
        pygame.draw.rect(cartao, (252, 250, 244), R(0, 0, 326, 368), border_radius=8)
        cartao.blit(foto, (13, 13))
        legenda = self.f_med if hasattr(self, "f_med") else pygame.font.Font(None, 28)
        texto(cartao, legenda, "Missão cumprida!", (90, 70, 50), (163, 338), "center")
        return pygame.transform.rotozoom(cartao, -3, 1.0)

    # ---------- entrada ----------
    def evento(self, ev):
        if ev.type == pygame.QUIT:
            self.rodando = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.rodando = False
            elif ev.key == pygame.K_r and self.estado in ("jogando", "comparando") and not self.pulo:
                self.reiniciar()
            elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.estado == "parabens":
                    self.ir_comparar()
                elif self.estado == "comparando":
                    self.proximo_nivel()
            elif self.estado == "jogando" and self.sel is not None and not self.pulo:
                if ev.key == pygame.K_c:
                    self.tentar_pulo("curto")
                elif ev.key == pygame.K_l:
                    self.tentar_pulo("longo")
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.clique(ev.pos)

    def clique(self, pos):
        if self.estado == "parabens":
            if self.botao_ver.clicado(pos):
                self.ir_comparar()
        elif self.estado == "comparando":
            if self.botao_prox.clicado(pos):
                self.proximo_nivel()
            elif self.botao_repetir.clicado(pos):
                self.reiniciar()
        elif self.estado == "jogando" and not self.pulo:
            if self.sel is not None:
                if self.botao_curto.clicado(pos):
                    self.tentar_pulo("curto")
                    return
                if self.botao_longo.clicado(pos):
                    self.tentar_pulo("longo")
                    return
            j = self.pedra_em(pos)
            if j is not None and j == self.sel:
                self.sel = None
            elif j is not None and self.alcancavel(j):
                self.sel = j
            else:
                self.sel = None

    def distancia(self, j):
        return self.rio.pos[j] - self.rio.pos[self.atual]

    def alcancavel(self, j):
        return j > self.atual and self.distancia(j) <= self.rio.Y

    def curto_ok(self, j):
        return self.distancia(j) <= self.rio.X

    def longo_ok(self, j):
        return self.distancia(j) <= self.rio.Y and self.c < self.rio.K

    def pedra_em(self, pos):
        mx, my = pos
        melhor, dmin = None, 1e9
        for j in range(self.rio.n):
            cx, w, topo = self.rio.x(j), self.rio.largura(j), self.rio.topo(j)
            if abs(mx - cx) <= max(w / 2, 16) + 4 and topo - 40 <= my <= topo + 38:
                if abs(mx - cx) < dmin:
                    melhor, dmin = j, abs(mx - cx)
        return melhor

    def tentar_pulo(self, tipo):
        j = self.sel
        if j is None:
            return
        ok = self.curto_ok(j) if tipo == "curto" else self.longo_ok(j)
        if ok:
            self.pulo = Pulo(self.rio, self.atual, j, tipo)
            self.sel = None

    def aterrissar(self):
        p = self.pulo
        self.pulo = None
        self.atual = p.j
        self.c = 0 if p.tipo == "curto" else self.c + 1
        self.saltos += 1
        self.historico.append((p.i, p.j, p.tipo))
        self.respingo(p.j)
        if p.j == self.rio.n - 1:
            self.estado = "parabens"
            self.iniciar_confete()
        else:
            self.encalhou = not any(
                self.alcancavel(j) and (self.curto_ok(j) or self.longo_ok(j))
                for j in range(self.atual + 1, self.rio.n))

    def respingo(self, j):
        if self.rio.margem(j):
            return
        x, y = self.rio.x(j), Y_PEDRA + 10
        self.aneis.append([x, y, 0.0])
        for _ in range(9):
            ang = random.uniform(math.pi * 1.15, math.pi * 1.85)
            v = random.uniform(70, 150)
            self.gotas.append([x, y, math.cos(ang) * v, math.sin(ang) * v, 0.0])

    def iniciar_confete(self):
        cores = [(255, 90, 90), (255, 200, 40), (90, 200, 255), (120, 230, 120), (240, 130, 220)]
        self.confete = [[random.uniform(0, LARGURA), random.uniform(-ALTURA, 0), random.uniform(90, 220),
                         random.choice(cores), random.uniform(6, 11), random.uniform(0, 6.28)]
                        for _ in range(130)]

    def ir_comparar(self):
        self.estado = "comparando"
        self.replay = {"i": 0, "idx": 0, "pulo": None, "espera": 0.8}

    def proximo_nivel(self):
        self.nivel += 1
        self.novo_rio()

    # ---------- atualizacao ----------
    def atualizar(self, dt):
        self.t += dt
        for n in self.nuvens:
            n[0] += n[3] * dt
            if n[0] > LARGURA + 140:
                n[0] = -160

        # peixe que pula la no fundo
        self.prox_peixe -= dt
        if self.peixe is None and self.prox_peixe <= 0:
            x0 = random.uniform(330, 560)
            self.peixe = {"x0": x0, "dx": random.uniform(60, 110), "y0": 372, "h": random.uniform(55, 80),
                          "t": 0.0, "dur": 1.1}
        if self.peixe:
            self.peixe["t"] += dt
            if self.peixe["t"] >= self.peixe["dur"]:
                self.peixe = None
                self.prox_peixe = random.uniform(5, 9)

        for a in self.aneis:
            a[2] += dt
        self.aneis = [a for a in self.aneis if a[2] < 0.9]
        for g in self.gotas:
            g[4] += dt
            g[0] += g[2] * dt
            g[1] += g[3] * dt
            g[3] += 520 * dt
        self.gotas = [g for g in self.gotas if g[4] < 0.55]

        if self.estado == "jogando" and self.pulo:
            self.pulo.t += dt
            if self.pulo.terminou():
                self.aterrissar()
        elif self.estado == "parabens":
            for c in self.confete:
                c[1] += c[2] * dt
                c[0] += math.sin(self.t * 2 + c[5]) * 30 * dt
                if c[1] > ALTURA + 20:
                    c[1] = -20
        elif self.estado == "comparando":
            self.atualizar_replay(dt)

    def atualizar_replay(self, dt):
        r = self.replay
        caminho = self.rio.caminho
        if r["pulo"]:
            r["pulo"].t += dt
            if r["pulo"].terminou():
                r["i"] = r["pulo"].j
                self.respingo(r["i"])
                r["pulo"] = None
                r["espera"] = 1.6 if r["i"] == self.rio.n - 1 else 0.35
        else:
            r["espera"] -= dt
            if r["espera"] <= 0:
                if r["i"] == self.rio.n - 1:
                    r["i"], r["idx"], r["espera"] = 0, 0, 0.6
                else:
                    i, j, tipo = caminho[r["idx"]]
                    r["pulo"] = Pulo(self.rio, i, j, tipo)
                    r["idx"] += 1

    # ---------- desenho ----------
    def desenhar(self):
        tela = self.tela
        mouse = pygame.mouse.get_pos()
        tela.blit(self.ceu, (0, 0))
        desenhar_sol(tela, self.t)
        for x, y, s, _ in self.nuvens:
            desenhar_nuvem(tela, x, y, s)
        tela.blit(self.chao, (0, 0))
        self.desenhar_agua()
        self.desenhar_peixe()

        rio = self.rio
        # pedras e rochas
        for j in range(rio.n):
            cx, w = rio.x(j), rio.largura(j)
            if rio.margem(j):
                desenhar_rocha(tela, cx, 480, w, 64, musgo=True)
            else:
                fase = (self.t * 0.5 + j * 0.37) % 1
                elipse_alpha(tela, (255, 255, 255, int(150 * (1 - fase))),
                             R(cx - (w + 8 + 22 * fase) / 2, Y_PEDRA + 4 - 3 * fase, w + 8 + 22 * fase, 12 + 6 * fase), 2)
                desenhar_rocha(tela, cx, Y_PEDRA, w, 24)

        for x, y, t in self.aneis:
            u = t / 0.9
            elipse_alpha(tela, (255, 255, 255, int(200 * (1 - u))), R(x - 14 - 46 * u, y - 4 - 8 * u, 28 + 92 * u, 8 + 16 * u), 3)

        if self.estado == "jogando":
            self.desenhar_aneis_alcance()
        if self.estado == "comparando":
            self.desenhar_caminhos()

        self.desenhar_sapo_cena(mouse)

        for x, y, vx, vy, t in self.gotas:
            pygame.draw.circle(tela, (225, 245, 255), (int(x), int(y)), 3)

        if self.estado == "jogando":
            self.desenhar_hud()
            self.desenhar_selecao(mouse)
            if self.encalhou and not self.pulo:
                r = R(LARGURA / 2 - 250, 150, 500, 40)
                painel(tela, r, (176, 70, 56))
                texto(tela, self.f_med, "O sapo encalhou! Aperte R pra recomeçar", CREME, r.center, "center", sombra=MARROM_ESC)
            self.desenhar_dica_rodape("Clique numa pedra e escolha o pulo   |   R recomeça   |   Esc sai")
        elif self.estado == "parabens":
            self.desenhar_parabens(mouse)
        elif self.estado == "comparando":
            self.desenhar_painel_comparacao(mouse)

    def desenhar_agua(self):
        # riscos claros que ficam balancando na agua
        for k in range(46):
            y = AGUA_TOPO + 30 + ((k * 53) % (ALTURA - AGUA_TOPO - 40))
            prof = (y - AGUA_TOPO) / (ALTURA - AGUA_TOPO)
            esq, dire = borda_esq(y) + 20, borda_dir(y) - 20
            x = esq + ((k * 197) % 1000) / 1000 * (dire - esq) + math.sin(self.t * 0.9 + k) * 10
            comp = 20 + 70 * prof
            elipse_alpha(self.tela, (215, 240, 255, 110), R(x, y, comp, 3 + 5 * prof), 2)

    def desenhar_peixe(self):
        p = self.peixe
        if not p:
            return
        u = p["t"] / p["dur"]
        x = p["x0"] + p["dx"] * u
        y = p["y0"] - 4 * p["h"] * u * (1 - u)
        dyu = -4 * p["h"] * (1 - 2 * u)
        ang = math.degrees(math.atan2(-dyu, p["dx"]))
        img = pygame.Surface((54, 26), pygame.SRCALPHA)
        pygame.draw.polygon(img, (214, 90, 34), [(0, 13), (14, 2), (14, 24)])
        pygame.draw.ellipse(img, (232, 118, 44), R(8, 2, 44, 22))
        pygame.draw.ellipse(img, (250, 170, 90), R(18, 5, 24, 8))
        pygame.draw.circle(img, BRANCO, (43, 10), 4)
        pygame.draw.circle(img, PRETO, (44, 10), 2)
        img = pygame.transform.rotate(img, ang)
        self.tela.blit(img, img.get_rect(center=(x, y)))

    def desenhar_aneis_alcance(self):
        pulso = 0.5 + 0.5 * math.sin(self.t * 5)
        for j in range(self.atual + 1, self.rio.n):
            if not self.alcancavel(j):
                continue
            if self.curto_ok(j):
                cor = (90, 230, 90)
            elif self.longo_ok(j):
                cor = (255, 200, 40)
            else:
                cor = (240, 90, 80)
            cx, w, topo = self.rio.x(j), self.rio.largura(j), self.rio.topo(j)
            ww = w + 16 + 4 * pulso
            elipse_alpha(self.tela, cor + (int(150 + 90 * pulso),), R(cx - ww / 2, topo - 6, ww, 34 + 8 * (self.rio.margem(j))), 3)
        # faixa embaixo do sapo mostrando os dois alcances
        cx, base = self.rio.x(self.atual), Y_PEDRA + 30
        ux = self.rio.unidade
        for alc, cor in ((self.rio.Y, (255, 200, 40)), (self.rio.X, (90, 230, 90))):
            faixa = R(cx, base + (0 if cor[0] > 200 else 8), alc * ux, 6)
            s = pygame.Surface((faixa.w, faixa.h), pygame.SRCALPHA)
            pygame.draw.rect(s, cor + (150,), s.get_rect(), border_radius=3)
            self.tela.blit(s, faixa.topleft)

    def pose_sapo(self):
        rio = self.rio
        if self.estado == "comparando":
            r = self.replay
            if r["pulo"]:
                return r["pulo"].pose(rio) + (False,)
            return rio.x(r["i"]), rio.topo(r["i"]) + 2, 1.0, 1.0 + 0.02 * math.sin(self.t * 3), False
        if self.pulo:
            return self.pulo.pose(rio) + (False,)
        cansado = self.estado == "jogando" and self.c >= rio.K
        return rio.x(self.atual), rio.topo(self.atual) + 2, 1.0, 1.0 + 0.02 * math.sin(self.t * 3), cansado

    def desenhar_sapo_cena(self, mouse):
        x, y, sx, sy, cansado = self.pose_sapo()
        if self.estado == "comparando":
            olhar = (1, 0)
        else:
            dx, dy = mouse[0] - x, mouse[1] - (y - 30)
            d = math.hypot(dx, dy) or 1
            olhar = (dx / d, dy / d)
        desenhar_sapo(self.tela, x, y, sx, sy, olhar, cansado, self.t)

    def desenhar_hud(self):
        rio = self.rio
        r = R(16, 16, 330, 132)
        painel(self.tela, r)
        texto(self.tela, self.f_med, f"Nível {self.nivel}", CREME, (30, 24), sombra=MARROM_ESC)
        texto(self.tela, self.f_med, f"Saltos: {self.saltos}", CREME, (196, 24), sombra=MARROM_ESC)
        texto(self.tela, self.f_peq, f"Curto até {rio.X}   •   Longo até {rio.Y}", CREME, (30, 64), sombra=MARROM_ESC)
        texto(self.tela, self.f_peq, f"Pernas (máx. {rio.K} longo{'s' if rio.K > 1 else ''} seguido{'s' if rio.K > 1 else ''}):", CREME, (30, 92), sombra=MARROM_ESC)
        for k in range(rio.K):
            cx = 40 + k * 28
            if k < rio.K - self.c:
                pygame.draw.circle(self.tela, BRANCO, (cx, 130), 11)
                pygame.draw.circle(self.tela, (110, 215, 90), (cx, 130), 9)
            else:
                pygame.draw.circle(self.tela, (110, 74, 40), (cx, 130), 11)
                pygame.draw.circle(self.tela, (130, 92, 56), (cx, 130), 8)

    def desenhar_dica_rodape(self, msg):
        img = self.f_peq.render(msg, True, BRANCO)
        r = img.get_rect(midbottom=(LARGURA // 2, ALTURA - 10)).inflate(26, 12)
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 50, 30, 150), s.get_rect(), border_radius=14)
        self.tela.blit(s, r.topleft)
        self.tela.blit(img, img.get_rect(center=r.center))

    def desenhar_selecao(self, mouse):
        j = self.sel
        if j is None or self.pulo:
            return
        rio = self.rio
        cx, topo = rio.x(j), rio.topo(j)
        # marcador na pedra escolhida
        pygame.draw.polygon(self.tela, BRANCO, [(cx - 9, topo - 62), (cx + 9, topo - 62), (cx, topo - 48)])
        bx = min(max(cx - 114, 10), LARGURA - 236)
        by = topo - 150
        self.botao_curto.rect.topleft = (bx, by)
        self.botao_longo.rect.topleft = (bx + 120, by)
        self.botao_curto.ativo = self.curto_ok(j)
        self.botao_longo.ativo = self.longo_ok(j)
        self.botao_curto.desenhar(self.tela, self.f_peq, mouse)
        self.botao_longo.desenhar(self.tela, self.f_peq, mouse)
        texto(self.tela, self.f_peq, f"distância {self.distancia(j)}", BRANCO, (bx + 114, by - 14), "midbottom", sombra=MARROM_ESC)
        if not self.curto_ok(j) and not self.longo_ok(j):
            texto(self.tela, self.f_peq, "perninhas cansadas! faça um curto antes", (255, 220, 200),
                  (bx + 114, by + 46), "midtop", sombra=MARROM_ESC)
        elif not self.curto_ok(j):
            texto(self.tela, self.f_peq, "longe demais pro curto", (255, 235, 200),
                  (bx + 114, by + 46), "midtop", sombra=MARROM_ESC)

    def desenhar_caminhos(self):
        rio = self.rio
        # jogador: por cima das pedras (laranja)
        for idx, (i, j, tipo) in enumerate(self.historico):
            dx = abs(rio.x(j) - rio.x(i))
            ap = desenhar_arco(self.tela, rio.x(i), rio.topo(i) - 6, rio.x(j), rio.topo(j) - 6,
                               22 + 0.28 * dx, LARANJA, 4, tipo == "longo")
            self.distintivo(ap, idx + 1, LARANJA)
        # otimo: por baixo, refletido na agua (roxo)
        for idx, (i, j, tipo) in enumerate(rio.caminho):
            dx = abs(rio.x(j) - rio.x(i))
            ap = desenhar_arco(self.tela, rio.x(i), Y_PEDRA + 20, rio.x(j), Y_PEDRA + 20,
                               22 + 0.28 * dx, ROXO, 4, tipo == "longo", baixo=True)
            self.distintivo(ap, idx + 1, ROXO)

    def distintivo(self, pos, numero, cor):
        pygame.draw.circle(self.tela, BRANCO, (int(pos[0]), int(pos[1])), 13)
        pygame.draw.circle(self.tela, cor, (int(pos[0]), int(pos[1])), 11)
        texto(self.tela, self.f_peq, str(numero), BRANCO, pos, "center")

    def desenhar_painel_comparacao(self, mouse):
        r = R(196, 14, 604, 178)
        painel(self.tela, r)
        voce, otimo = self.saltos, self.rio.otimo
        texto(self.tela, self.f_gra, "Sua travessia x solução ótima", CREME, (498, 40), "center", sombra=MARROM_ESC)
        pygame.draw.line(self.tela, LARANJA, (240, 78), (290, 78), 5)
        texto(self.tela, self.f_peq, f"Você: {voce} saltos (em cima)", CREME, (300, 78), "midleft", sombra=MARROM_ESC)
        pygame.draw.line(self.tela, ROXO, (508, 78), (558, 78), 5)
        texto(self.tela, self.f_peq, f"Ótimo: {otimo} saltos (embaixo)", CREME, (568, 78), "midleft", sombra=MARROM_ESC)
        if voce == otimo:
            veredito = "Perfeito! Você igualou a solução ótima!"
        else:
            veredito = f"Dava pra fazer com {voce - otimo} salto(s) a menos. Veja o caminho roxo!"
        texto(self.tela, self.f_peq, veredito, (255, 236, 170), (498, 101), "center", sombra=MARROM_ESC)
        texto(self.tela, self.f_peq, "(tracejado = salto longo)", CREME, (498, 120), "center", sombra=MARROM_ESC)
        self.botao_repetir.desenhar(self.tela, self.f_peq, mouse)
        self.botao_prox.desenhar(self.tela, self.f_peq, mouse)

    def desenhar_parabens(self, mouse):
        s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        s.fill((10, 30, 20, 165))
        self.tela.blit(s, (0, 0))
        for x, y, v, cor, tam, fase in self.confete:
            pygame.draw.rect(self.tela, cor, R(x, y, tam, tam * 0.6))
        pulso = 1 + 0.04 * math.sin(self.t * 4)
        titulo = pygame.transform.rotozoom(
            self.f_enorme.render("Parabéns!", True, (255, 222, 70)), 0, pulso)
        borda = pygame.transform.rotozoom(
            self.f_enorme.render("Parabéns!", True, MARROM_ESC), 0, pulso)
        r = titulo.get_rect(center=(LARGURA // 2, 62))
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (3, 3), (-3, 3)):
            self.tela.blit(borda, r.move(dx, dy))
        self.tela.blit(titulo, r)
        self.tela.blit(self.polaroid, self.polaroid.get_rect(center=(LARGURA // 2, 332)))
        texto(self.tela, self.f_med, f"Você atravessou o rio em {self.saltos} saltos!", BRANCO,
              (LARGURA // 2, 545), "center", sombra=MARROM_ESC)
        self.botao_ver.desenhar(self.tela, self.f_med, mouse)


def main():
    jogo = Jogo()
    while jogo.rodando:
        dt = min(jogo.relogio.tick(FPS) / 1000, 0.05)
        for ev in pygame.event.get():
            jogo.evento(ev)
        jogo.atualizar(dt)
        jogo.desenhar()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()