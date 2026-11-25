"""Desvie dos Meteoros: modo Arcade e campanha com fases persistentes."""

import json
import math
import random
from pathlib import Path

import pygame


LARGURA, ALTURA = 800, 600
FPS = 60
ARQUIVO_SAVE = Path(__file__).with_name("save.json")
FUNDO = (8, 12, 31)
BRANCO = (240, 244, 255)
CIANO = (70, 220, 245)
LARANJA = (255, 145, 65)

# Os recortes apontam para os sprites dentro das imagens JPG fornecidas.
PASTA_IMAGENS = Path(__file__).with_name("Images")
PLANETAS = [
    {"nome": "Terra", "arquivo": "earth.jpg", "recorte": (608, 0, 1536, 1536), "cor": (48, 125, 205)},
    {"nome": "Marte", "arquivo": "marcs.jpg", "recorte": (608, 0, 1536, 1536), "cor": (190, 80, 55)},
    {"nome": "Jupiter", "arquivo": "jupter.jpg", "recorte": (608, 0, 1536, 1536), "cor": (190, 145, 105)},
    {"nome": "Saturno", "arquivo": "outros_planetas.jpg", "recorte": (0, 0, 1376, 768), "cor": (210, 180, 105)},
    {"nome": "Netuno", "arquivo": "outros_planetas.jpg", "recorte": (1376, 0, 1376, 768), "cor": (55, 90, 210)},
    {"nome": "Venus", "arquivo": "outros_planetas.jpg", "recorte": (0, 768, 1376, 768), "cor": (205, 145, 75)},
    {"nome": "Urano", "arquivo": "outros_planetas.jpg", "recorte": (1376, 768, 1376, 768), "cor": (80, 185, 190)},
]
TOTAL_FASES = len(PLANETAS) - 1
ARQUIVOS_METEOROS = {
    1: ("meteoros 1 a 2 e 2 a 3.jpg", 0),
    2: ("meteoros 1 a 2 e 2 a 3.jpg", 1),
    3: ("meteoros 3 a 4 e 4 a 5.jpg", 0),
    4: ("meteoros 3 a 4 e 4 a 5.jpg", 1),
}
SPRITES_PLANETAS = []
SPRITES_METEOROS = {}
CACHE_ESCALA = {}


def carregar_progresso():
    """Carrega recorde e fases liberadas, aceitando tambem o save antigo."""
    try:
        dados = json.loads(ARQUIVO_SAVE.read_text(encoding="utf-8"))
        return {
            "recorde": max(0, int(dados.get("recorde", 0))),
            "fases_liberadas": max(1, min(TOTAL_FASES, int(dados.get("fases_liberadas", 1)))),
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {"recorde": 0, "fases_liberadas": 1}


def salvar_progresso(progresso):
    temporario = ARQUIVO_SAVE.with_suffix(".tmp")
    temporario.write_text(json.dumps(progresso, indent=2), encoding="utf-8")
    temporario.replace(ARQUIVO_SAVE)


def texto(tela, fonte, mensagem, y, cor=BRANCO, centro_x=LARGURA // 2):
    imagem = fonte.render(mensagem, True, cor)
    tela.blit(imagem, imagem.get_rect(center=(centro_x, y)))


def remover_fundo_branco(imagem):
    """Torna transparente apenas o branco conectado as bordas do recorte."""
    fundo = pygame.mask.from_threshold(imagem, (255, 255, 255), (35, 35, 35, 0))
    fundo = fundo.connected_component((0, 0))
    alpha = fundo.to_surface(setcolor=(255, 255, 255, 0), unsetcolor=(255, 255, 255, 255))
    imagem.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    limites = imagem.get_bounding_rect(min_alpha=1)
    if limites.width and limites.height:
        return imagem.subsurface(limites).copy()
    return imagem


def preparar_recorte(origem, recorte, caixa_tamanho):
    x, y, largura, altura = recorte
    origem = origem.subsurface(pygame.Rect(x, y, largura, altura)).copy()
    max_largura, max_altura = caixa_tamanho
    escala = min(max_largura / largura, max_altura / altura)
    tamanho = (max(1, int(largura * escala)), max(1, int(altura * escala)))
    sprite = pygame.transform.smoothscale(origem, tamanho).convert_alpha()
    return remover_fundo_branco(sprite)


def carregar_sprite(arquivo, recorte, caixa_tamanho):
    origem = pygame.image.load(str(PASTA_IMAGENS / arquivo)).convert()
    return preparar_recorte(origem, recorte, caixa_tamanho)


def carregar_arte():
    global SPRITES_PLANETAS, SPRITES_METEOROS
    SPRITES_PLANETAS = [
        carregar_sprite(planeta["arquivo"], planeta["recorte"], (220, 180))
        for planeta in PLANETAS
    ]
    SPRITES_METEOROS = {}
    sheets = {}
    for fase, (arquivo, linha) in ARQUIVOS_METEOROS.items():
        if arquivo not in sheets:
            sheets[arquivo] = pygame.image.load(str(PASTA_IMAGENS / arquivo)).convert()
        sheet = sheets[arquivo]
        sprites = []
        for coluna in range(3):
            x0 = round(coluna * sheet.get_width() / 3)
            x1 = round((coluna + 1) * sheet.get_width() / 3)
            y0 = linha * (sheet.get_height() // 2)
            y1 = (linha + 1) * (sheet.get_height() // 2)
            sprites.append(preparar_recorte(sheet, (x0, y0, x1 - x0, y1 - y0), (96, 84)))
        SPRITES_METEOROS[fase] = sprites


def imagem_dimensionada(sprite, tamanho):
    chave = (id(sprite), tamanho)
    if chave not in CACHE_ESCALA:
        CACHE_ESCALA[chave] = pygame.transform.smoothscale(sprite, tamanho)
    return CACHE_ESCALA[chave]


def desenhar_planeta(tela, centro, raio, indice):
    sprite = SPRITES_PLANETAS[indice % len(SPRITES_PLANETAS)]
    largura, altura = sprite.get_size()
    fator = min(raio * 2.8 / largura, raio * 2.1 / altura)
    tamanho = (max(1, int(largura * fator)), max(1, int(altura * fator)))
    sprite = imagem_dimensionada(sprite, tamanho)
    tela.blit(sprite, sprite.get_rect(center=centro))


def desenhar_nave(tela, x, y):
    pontos = [(x, y - 24), (x - 19, y + 19), (x, y + 11), (x + 19, y + 19)]
    pygame.draw.polygon(tela, CIANO, pontos)
    pygame.draw.polygon(tela, BRANCO, pontos, 2)
    pygame.draw.circle(tela, (180, 250, 255), (int(x), int(y - 4)), 5)


def novo_meteoro(nivel, fase=None, variacao=None):
    raio = random.randint(14, min(31 + nivel, 43))
    x = random.randint(raio, LARGURA - raio)
    if variacao is None:
        variacao = random.randrange(3)
    sprite = SPRITES_METEOROS.get(fase, [None, None, None])[variacao]
    sprite_base = None
    sprite_rotacionado = None
    if sprite:
        largura, altura = sprite.get_size()
        caixa = raio * 2 + 12
        fator = min(caixa / largura, caixa / altura)
        tamanho = (max(1, int(largura * fator)), max(1, int(altura * fator)))
        sprite_base = imagem_dimensionada(sprite, tamanho)
        sprite_rotacionado = pygame.transform.rotate(sprite_base, 0)
    return {"x": float(x), "y": float(-raio), "raio": raio,
            "velocidade": random.uniform(190 + nivel * 16, 300 + nivel * 24),
            "sprite": sprite, "tipo": variacao, "angulo": 0.0,
            "velocidade_rotacao": random.choice((-65.0, -45.0, 45.0, 65.0)),
            "sprite_base": sprite_base, "sprite_rotacionado": sprite_rotacionado,
            "rotacao_aplicada": 0}


def iniciar_partida(modo, fase=1):
    return {
        "modo": modo, "fase": fase, "tempo": 0.0, "tempo_spawn": 0.0,
        "nave_x": LARGURA / 2, "nave_y": ALTURA - 65, "meteoros": [],
        "meteoros_vencidos": 0, "meteoros_criados": 0, "fila_tipos": [],
    }


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    carregar_arte()
    pygame.display.set_caption("Desvie dos Meteoros")
    relogio = pygame.time.Clock()
    fonte = pygame.font.Font(None, 32)
    fonte_grande = pygame.font.Font(None, 64)
    fonte_media = pygame.font.Font(None, 40)
    fonte_menor = pygame.font.Font(None, 24)

    progresso = carregar_progresso()
    fase_selecionada = progresso["fases_liberadas"]
    menu_selecionado = 0
    estrelas = [(random.randrange(LARGURA), random.randrange(ALTURA), random.choice((1, 1, 2))) for _ in range(90)]
    estado = "menu"
    partida = None
    rodando = True

    while rodando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.05)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                if partida and partida["modo"] == "arcade":
                    progresso["recorde"] = max(progresso["recorde"], int(partida["tempo"]))
                salvar_progresso(progresso)
                rodando = False
                continue
            if evento.type != pygame.KEYDOWN:
                continue

            if evento.key == pygame.K_ESCAPE:
                if estado == "jogando":
                    estado = "pausado"
                elif estado == "pausado":
                    estado = "jogando"
                elif estado == "fases":
                    estado = "menu"
                elif estado in ("menu", "fim", "fase_completa"):
                    estado = "menu"

            elif estado == "menu":
                if evento.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d, pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                    menu_selecionado = 1 - menu_selecionado
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if menu_selecionado == 0:
                        partida = iniciar_partida("arcade")
                        estado = "jogando"
                    else:
                        fase_selecionada = progresso["fases_liberadas"]
                        estado = "fases"

            elif estado == "fases":
                if evento.key in (pygame.K_LEFT, pygame.K_a):
                    fase_selecionada = max(1, fase_selecionada - 1)
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    fase_selecionada = min(progresso["fases_liberadas"], fase_selecionada + 1)
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    partida = iniciar_partida("fases", fase_selecionada)
                    estado = "jogando"

            elif estado in ("fim", "fase_completa"):
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if estado == "fim":
                        partida = iniciar_partida(partida["modo"], partida["fase"])
                        estado = "jogando"
                    elif partida["fase"] < TOTAL_FASES:
                        estado = "fases"
                    else:
                        estado = "menu"

        if estado == "jogando":
            teclas = pygame.key.get_pressed()
            dx = int(teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) - int(teclas[pygame.K_LEFT] or teclas[pygame.K_a])
            dy = int(teclas[pygame.K_DOWN] or teclas[pygame.K_s]) - int(teclas[pygame.K_UP] or teclas[pygame.K_w])
            partida["nave_x"] = max(22, min(LARGURA - 22, partida["nave_x"] + dx * 390 * dt))
            partida["nave_y"] = max(30, min(ALTURA - 28, partida["nave_y"] + dy * 390 * dt))
            partida["tempo"] += dt

            if partida["modo"] == "arcade":
                nivel = int(partida["tempo"] // 20)
                planeta = (int(partida["tempo"] // 25)) % len(PLANETAS)
            else:
                nivel = partida["fase"] - 1
                planeta = partida["fase"] % len(PLANETAS)

            partida["tempo_spawn"] += dt
            intervalo = max(0.25, 0.85 - nivel * 0.08 - (partida["tempo"] * 0.003 if partida["modo"] == "arcade" else 0))
            alvo_meteoros = 12 + partida["fase"] * 3 if partida["modo"] == "fases" else None
            ainda_pode_spawnar = partida["modo"] == "arcade" or partida["meteoros_criados"] < alvo_meteoros
            if partida["tempo_spawn"] >= intervalo and ainda_pode_spawnar:
                fase_sprite = (partida["fase"] if partida["modo"] == "fases"
                               else int(partida["tempo"] // 25) % 4 + 1)
                if partida["modo"] == "fases":
                    if not partida["fila_tipos"]:
                        partida["fila_tipos"] = random.sample((0, 1, 2), 3)
                    tipo = partida["fila_tipos"].pop()
                else:
                    tipo = None
                partida["meteoros"].append(novo_meteoro(nivel, fase_sprite, tipo))
                partida["meteoros_criados"] += 1
                partida["tempo_spawn"] = 0.0
            for meteoro in partida["meteoros"]:
                meteoro["y"] += meteoro["velocidade"] * dt
                meteoro["angulo"] = (meteoro["angulo"] + meteoro["velocidade_rotacao"] * dt) % 360
                novo_angulo = int(meteoro["angulo"] // 4) * 4
                if meteoro["sprite_base"] and novo_angulo != meteoro["rotacao_aplicada"]:
                    meteoro["sprite_rotacionado"] = pygame.transform.rotate(meteoro["sprite_base"], novo_angulo)
                    meteoro["rotacao_aplicada"] = novo_angulo
            if partida["modo"] == "fases":
                partida["meteoros_vencidos"] += sum(
                    1 for m in partida["meteoros"] if m["y"] >= ALTURA + m["raio"]
                )
            partida["meteoros"] = [m for m in partida["meteoros"] if m["y"] < ALTURA + m["raio"]]

            colisao = False
            for meteoro in partida["meteoros"]:
                dx = partida["nave_x"] - meteoro["x"]
                dy = partida["nave_y"] - 3 - meteoro["y"]
                if dx * dx + dy * dy < (meteoro["raio"] + 14) ** 2:
                    colisao = True
                    break
            if colisao:
                estado = "fim"
                if partida["modo"] == "arcade":
                    recorde = max(progresso["recorde"], int(partida["tempo"]))
                    progresso["recorde"] = recorde
                salvar_progresso(progresso)
            elif partida["modo"] == "fases" and partida["meteoros_vencidos"] >= 12 + partida["fase"] * 3:
                estado = "fase_completa"
                progresso["fases_liberadas"] = max(progresso["fases_liberadas"], min(TOTAL_FASES, partida["fase"] + 1))
                fase_selecionada = progresso["fases_liberadas"]
                salvar_progresso(progresso)

        tela.fill(FUNDO)
        for sx, sy, tamanho in estrelas:
            pygame.draw.circle(tela, (95, 115, 160), (sx, sy), tamanho)

        if partida and estado in ("jogando", "pausado", "fim", "fase_completa"):
            if partida["modo"] == "fases":
                origem = partida["fase"] - 1
                destino = partida["fase"]
                desenhar_planeta(tela, (78, 120), 30, origem)
                desenhar_planeta(tela, (722, 120), 38, destino)
                texto(tela, fonte_menor, PLANETAS[origem]["nome"], 166, centro_x=78)
                texto(tela, fonte_menor, PLANETAS[destino]["nome"], 166, CIANO, centro_x=722)
                texto(tela, fonte, f"FASE {partida['fase']}: VIAGEM ENTRE PLANETAS", 43, CIANO)
                pygame.draw.line(tela, (80, 110, 150), (115, 120), (685, 120), 3)
                alvo_meteoros = 12 + partida["fase"] * 3
                largura_barra = int(570 * min(1, partida["meteoros_vencidos"] / alvo_meteoros))
                pygame.draw.rect(tela, CIANO, (115, 116, largura_barra, 8), border_radius=4)
                texto(tela, fonte_menor,
                      f"Meteoros vencidos: {partida['meteoros_vencidos']}/{alvo_meteoros}", 194, BRANCO)
            else:
                planeta = (int(partida["tempo"] // 25)) % len(PLANETAS)
                desenhar_planeta(tela, (720, 110), 42, planeta)
                texto(tela, fonte, f"ARCADE  |  {PLANETAS[planeta]['nome']}", 43, CIANO)
                texto(tela, fonte_menor, f"Setor {int(partida['tempo'] // 20) + 1}", 166, centro_x=720)

            for meteoro in partida["meteoros"]:
                centro = (int(meteoro["x"]), int(meteoro["y"]))
                sprite = meteoro["sprite"]
                if sprite:
                    sprite_tela = meteoro["sprite_rotacionado"]
                    tela.blit(sprite_tela, sprite_tela.get_rect(center=centro))
                else:
                    cores_tipo = ((255, 145, 65), (218, 99, 64), (177, 137, 104))
                    cor_meteoro = cores_tipo[meteoro["tipo"]]
                    pygame.draw.circle(tela, cor_meteoro, centro, meteoro["raio"])
                    pygame.draw.circle(tela, (75, 55, 54), centro, meteoro["raio"], 2)
                    angulo = math.radians(meteoro["angulo"])
                    marca = (centro[0] + int(math.cos(angulo) * meteoro["raio"] * 0.4),
                             centro[1] + int(math.sin(angulo) * meteoro["raio"] * 0.4))
                    pygame.draw.circle(tela, (205, 115, 70), marca, max(3, meteoro["raio"] // 4))
            desenhar_nave(tela, int(partida["nave_x"]), int(partida["nave_y"]))
            if partida["modo"] == "arcade":
                tela.blit(fonte.render(f"Tempo: {int(partida['tempo'])}s", True, BRANCO), (20, 18))
                tela.blit(fonte.render(f"Recorde Arcade: {progresso['recorde']}s", True, CIANO), (20, 50))

        if estado == "menu":
            texto(tela, fonte_grande, "DESVIE DOS METEOROS", 100, CIANO)
            texto(tela, fonte, "ESCOLHA SEU MODO", 170, (175, 190, 220))

            arcade_card = pygame.Rect(105, 235, 280, 190)
            fases_card = pygame.Rect(415, 235, 280, 190)
            pygame.draw.rect(tela, (17, 27, 54), arcade_card, border_radius=18)
            pygame.draw.rect(tela, (17, 27, 54), fases_card, border_radius=18)

            planeta_maximo = progresso["fases_liberadas"]
            desenhar_planeta(tela, (fases_card.centerx + 62, fases_card.centery + 4), 72, planeta_maximo)
            pygame.draw.rect(tela, (8, 12, 31), (fases_card.x + 12, fases_card.y + 18, 145, 150), border_radius=12)

            arcade_cor = LARANJA if menu_selecionado == 0 else BRANCO
            fases_cor = CIANO if menu_selecionado == 1 else BRANCO
            arcade_fonte = fonte_media if menu_selecionado == 0 else fonte
            fases_fonte = fonte
            texto(tela, arcade_fonte, "MODELO ARCADE", arcade_card.centery - 20, arcade_cor, arcade_card.centerx)
            texto(tela, fonte_menor, "Sobreviva e aumente seu recorde", arcade_card.centery + 22, BRANCO, arcade_card.centerx)
            texto(tela, fases_fonte, "MODO FASES", fases_card.centery - 20, fases_cor, fases_card.x + 82)
            texto(tela, fonte_menor, "Viagens entre planetas", fases_card.centery + 18, BRANCO, fases_card.x + 84)

            texto(tela, fonte, f"Recorde: {progresso['recorde']}s", 460, LARANJA, arcade_card.centerx)
            texto(tela, fonte_menor, f"Maior fase liberada: {progresso['fases_liberadas']} - {PLANETAS[planeta_maximo]['nome']}", 460, CIANO, fases_card.centerx)

            if menu_selecionado == 0:
                pygame.draw.rect(tela, BRANCO, arcade_card, 3, border_radius=18)
            else:
                pygame.draw.rect(tela, BRANCO, fases_card, 3, border_radius=18)
            texto(tela, fonte, "Setas ou A/D: escolher  |  ENTER ou ESPACO: iniciar", 525, BRANCO)
            texto(tela, fonte_menor, "ESC para sair", 560, (170, 180, 205))
        elif estado == "fases":
            texto(tela, fonte_grande, "SELECAO DE FASES", 95, CIANO)
            texto(tela, fonte, "Escolha uma viagem entre os planetas liberados", 145)
            for fase in range(1, TOTAL_FASES + 1):
                coluna = (fase - 1) % 4
                linha = (fase - 1) // 4
                x, y = 115 + coluna * 190, 260 + linha * 150
                desbloqueada = fase <= progresso["fases_liberadas"]
                cor = CIANO if desbloqueada else (100, 105, 120)
                if fase == fase_selecionada:
                    pygame.draw.rect(tela, BRANCO, (x - 69, y - 65, 138, 125), 3, border_radius=12)
                desenhar_planeta(tela, (x, y - 32), 24, fase)
                texto(tela, fonte, f"{fase}: {PLANETAS[fase]['nome']}", y + 10, cor, x)
                texto(tela, fonte_menor, "LIBERADA" if desbloqueada else "BLOQUEADA", y + 37, cor, x)
            texto(tela, fonte_menor, f"Selecionada: Fase {fase_selecionada}  |  {PLANETAS[fase_selecionada - 1]['nome']} -> {PLANETAS[fase_selecionada]['nome']}", 490, BRANCO)
            texto(tela, fonte_menor, "Setas ou A/D: trocar fase  |  ENTER: iniciar viagem", 520, BRANCO)
            texto(tela, fonte_menor, "ESC para voltar", 550, (170, 180, 205))
        elif estado == "pausado":
            texto(tela, fonte_grande, "JOGO PAUSADO", ALTURA // 2 - 20, CIANO)
            texto(tela, fonte, "ESC para continuar", ALTURA // 2 + 35)
        elif estado == "fim":
            texto(tela, fonte_grande, "FIM DE JOGO", ALTURA // 2 - 75, LARANJA)
            if partida["modo"] == "fases":
                texto(tela, fonte, f"Meteoros vencidos: {partida['meteoros_vencidos']}/{12 + partida['fase'] * 3}", ALTURA // 2 - 15)
                texto(tela, fonte, f"A fase {partida['fase']} continua bloqueada ate ser concluida", ALTURA // 2 + 25)
            else:
                texto(tela, fonte, f"Sobreviveu por {int(partida['tempo'])} segundos", ALTURA // 2 - 15)
                texto(tela, fonte, f"Recorde: {progresso['recorde']}s", ALTURA // 2 + 25, CIANO)
            texto(tela, fonte, "ENTER para tentar novamente", ALTURA // 2 + 85)
            texto(tela, fonte_menor, "ESC para voltar ao menu", ALTURA // 2 + 125, (170, 180, 205))
        elif estado == "fase_completa":
            texto(tela, fonte_grande, "DESTINO ALCANCADO!", ALTURA // 2 - 70, CIANO)
            texto(tela, fonte_media, f"Fase {partida['fase']} concluida", ALTURA // 2)
            texto(tela, fonte, f"Meteoros vencidos: {partida['meteoros_vencidos']}", ALTURA // 2 + 35, BRANCO)
            if partida["fase"] < TOTAL_FASES:
                texto(tela, fonte, f"Fase {partida['fase'] + 1} liberada: {PLANETAS[partida['fase'] + 1]['nome']}", ALTURA // 2 + 70, BRANCO)
                texto(tela, fonte, "ENTER para selecionar a proxima viagem", ALTURA // 2 + 115)
            else:
                texto(tela, fonte, "Voce concluiu todas as viagens!", ALTURA // 2 + 70, BRANCO)
                texto(tela, fonte, "ENTER para voltar ao menu", ALTURA // 2 + 115)
            texto(tela, fonte_menor, "Progresso salvo automaticamente", ALTURA // 2 + 155, (170, 180, 205))

        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
