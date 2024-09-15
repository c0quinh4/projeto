import pygame as pg
import numpy as np
from numba import njit

class Kart:
    def __init__(self):
        # Inicialização das variáveis do kart
        self.posx, self.posy, self.rot, self.vel = 27, 18.5, 4.7, 0  # Posição inicial ajustada
        self.acceleration = 0.00001
        self.deceleration = 0.00001
        self.brake_deceleration = 0.0003
        self.max_speed = 0.01
        self.min_speed = -0.005
        self.slow_down_factor = 0.95  # Redução de velocidade fora da pista

    def update(self, keys, et, on_track, on_border):
        # Atualiza a rotação com base nas teclas de direção
        self.rot += 0.0015 * et * (keys[pg.K_RIGHT] or keys[ord('d')] - (keys[pg.K_LEFT] or keys[ord('a')]))

        # Aceleração com a tecla W (ou seta para cima)
        if keys[pg.K_UP] or keys[ord('w')]:
            if on_border:
                self.vel = 0  # Impede o movimento para frente na borda
            else:
                self.vel = min(self.vel + self.acceleration * et, self.max_speed)

        # Frenagem com a tecla S (ou seta para baixo)
        elif keys[pg.K_DOWN] or keys[ord('s')]:
            if self.vel > 0:
                self.vel = max(self.vel - self.brake_deceleration * et, 0)
            else:
                self.vel = max(self.vel - self.acceleration * et, self.min_speed)

        # Desaceleração suave quando nem W nem S são pressionados
        else:
            if self.vel > 0:
                self.vel = max(self.vel - self.deceleration * et, 0)
            elif self.vel < 0:
                self.vel = min(self.vel + self.deceleration * et, 0)

        # Atualiza a posição do kart
        new_posx = self.posx + np.cos(self.rot) * self.vel * et
        new_posy = self.posy + np.sin(self.rot) * self.vel * et

        # Atualiza posição e velocidade considerando borda
        if on_border and (keys[pg.K_UP] or keys[ord('w')]):  # Bloqueia avanço na borda
            self.vel = 0
        else:
            self.posx = new_posx
            self.posy = new_posy

class Renderer:
    def __init__(self, hres, halfvres):
        # Inicializa as variáveis de resolução e carrega as texturas
        self.hres, self.halfvres = hres, halfvres
        self.mod = hres / 60
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))
        self.load_assets()

    def load_assets(self):
        # Carrega as texturas do céu, chão, pista e bordas
        self.sky = pg.surfarray.array3d(pg.transform.scale(pg.image.load('assets/skybox.jpg'), (360, self.halfvres * 2))) / 255
        self.floor = pg.surfarray.array3d(pg.image.load('assets/MarioKart.png')) / 255
        self.track_surface = pg.surfarray.array3d(pg.image.load('assets/pista.png').convert_alpha()) / 255
        self.border_surface = pg.surfarray.array3d(pg.image.load('assets/borda.png').convert_alpha()) / 255
        self.floor_width, self.floor_height = self.floor.shape[0], self.floor.shape[1]

    def render_frame(self, posx, posy, rot):
        # Renderiza o frame atual com base na posição e rotação do kart
        self.frame = new_frame(posx, posy, rot, self.frame, self.sky, self.floor, self.track_surface, self.border_surface, self.hres, self.halfvres, self.mod)
        return pg.surfarray.make_surface(self.frame * 255)

    def is_on_track(self, posx, posy):
        # Verifica se o kart está sobre a área da textura "pista"
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        return np.mean(self.track_surface[xx][yy]) > 0.5

    def is_on_border(self, posx, posy):
        # Verifica se o kart está nas áreas coloridas da borda (ignorar centro preto)
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        if (yy < 5 or yy > 973) or (xx < 5 or xx > 973):
            return True
        return False

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, border_surface, hres, halfvres, mod):
    for i in range(hres):
        rot_i = rot + np.deg2rad(i / mod - 30)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(np.deg2rad(i / mod - 30))
        frame[i][:] = sky[int(np.rad2deg(rot_i) % 359)][:]
        for j in range(halfvres):
            n = (halfvres / (halfvres - j)) / cos2
            x, y = posx + cos * n, posy + sin * n
            xx, yy = int(x / 30 % 1 * 1023), int(y / 30 % 1 * 1023)
            shade = 0.95 + 0.05 * (1 - j / halfvres)
            frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade
    return frame

class SoundManager:
    def __init__(self):
        # Gerencia a música de fundo
        pg.mixer.music.load('assets/musica.mp3')
        pg.mixer.music.play(-1)
        pg.mixer.music.set_volume(0.08)

class Game:
    def __init__(self):
        # Inicializa o Pygame, a tela e os elementos do jogo
        pg.init()
        self.screen = pg.display.set_mode((800, 600))
        self.clock = pg.time.Clock()
        self.kart = Kart()
        self.renderer = Renderer(120, 100)
        self.sound_manager = SoundManager()
        self.load_sprites()
        self.running = True
        self.controls_enabled = False  # Controles inicialmente desativados
        self.lap_count = 0  # Contador de voltas
        self.has_crossed_finish_line = False  # Verificação para evitar contagem de volta múltipla

        # Inicializa a fonte
        pg.font.init()
        self.font = pg.font.SysFont('Arial', 24)

        # Carrega o countdown assets e som
        self.countdown_images = [
            pg.image.load('assets/3.png'),
            pg.image.load('assets/2.png'),
            pg.image.load('assets/1.png'),
            pg.image.load('assets/go.png')
        ]
        self.countdown_sound = 'assets/ct.mp3'  # Som do countdown

    def load_sprites(self):
        # Carrega os sprites do Mario e do kart
        mario_sheet = pg.image.load('assets/mario_sheet.png').convert_alpha()
        sprite_width, sprite_height, sprite_scale = 32, 32, 6.5
        self.mario_w = pg.transform.scale(mario_sheet.subsurface(pg.Rect(5.55 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
                                          (sprite_width * sprite_scale, sprite_height * sprite_scale))
        self.mario_a = pg.transform.scale(mario_sheet.subsurface(pg.Rect(4.6 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
                                          (sprite_width * sprite_scale, sprite_height * sprite_scale))
        self.mario_d = pg.transform.scale(mario_sheet.subsurface(pg.Rect(7.38 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
                                          (sprite_width * sprite_scale, sprite_height * sprite_scale))
        self.kart_sprite = pg.transform.scale(pg.image.load('assets/kart.png'), (200, 200))
        self.current_sprite = self.mario_w  # Sprite inicial

    def handle_input(self):
        # Gerencia a entrada do jogador e atualiza o sprite correspondente
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[ord('a')]:
            self.current_sprite = self.mario_a
        elif keys[pg.K_RIGHT] or keys[ord('d')]:
            self.current_sprite = self.mario_d
        elif keys[pg.K_DOWN] or keys[ord('s')]:
            self.current_sprite = self.kart_sprite
        else:
            self.current_sprite = self.mario_w

    def draw_text(self, text, x, y):
        # Renderiza o texto na tela
        text_surface = self.font.render(text, True, (255, 255, 255))  # Texto branco
        self.screen.blit(text_surface, (x, y))

    def countdown(self):
        # Toca o som do countdown
        pg.mixer.music.load(self.countdown_sound)
        pg.mixer.music.play()

        # Exibe o countdown de 3, 2, 1 e Go por cima da tela do jogo
        for i in range(4):
            # Renderiza o cenário e os sprites do jogo
            self.render_game_frame()

            # Sobrepõe o countdown sobre o jogo
            self.screen.blit(self.countdown_images[i], (400 - self.countdown_images[i].get_width() // 2, 300 - self.countdown_images[i].get_height() // 2))
            pg.display.update()
            pg.time.wait(1000)  # Espera 1 segundo por imagem

        # Aguarda o fim do som do countdown
        while pg.mixer.music.get_busy():
            pg.time.wait(100)

        # Inicia a música de fundo
        self.sound_manager = SoundManager()
        self.controls_enabled = True  # Habilita os controles após o countdown

    def check_finish_line(self):
        # Coordenadas da linha de chegada
        finish_line_x_min = 26.25
        finish_line_x_max = 28.7
        finish_line_y = 17.5

        # Verifica se o kart está sobre a linha de chegada
        if finish_line_x_min <= self.kart.posx <= finish_line_x_max and abs(self.kart.posy - finish_line_y) < 0.1:
            # Verifica se o kart está se movendo para frente
            if self.kart.vel > 0:
                # Se o kart cruzar a linha de chegada e ainda não foi contabilizado
                if not self.has_crossed_finish_line:
                    self.lap_count += 1  # Incrementa o contador de voltas
                    self.has_crossed_finish_line = True  # Marca que cruzou a linha de chegada
            else:
                self.has_crossed_finish_line = False  # Permite contar nova volta se o kart for para trás
        else:
            self.has_crossed_finish_line = False  # Reseta se o kart saiu da linha de chegada

    def render_game_frame(self):
        # Atualiza o estado do jogo sem controle do usuário
        et = self.clock.tick()  # Tempo entre frames

        # Renderiza o cenário
        frame_surface = self.renderer.render_frame(self.kart.posx, self.kart.posy, self.kart.rot)
        frame_surface = pg.transform.scale(frame_surface, (800, 600))
        self.screen.blit(frame_surface, (0, 0))

        # Desenha o sprite do kart
        sprite_rect = self.current_sprite.get_rect(center=(400, 600 - 120))
        self.screen.blit(self.current_sprite, sprite_rect)

        # Mostra a posição x e y do kart no canto superior esquerdo com duas casas decimais
        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)

        # Mostra o número de voltas no canto superior esquerdo
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)

    def run(self):
        # Executa o countdown antes de começar o jogo
        self.countdown()

        # Loop principal do jogo
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.running = False

            # Apenas permite controle após o countdown
            if self.controls_enabled:
                self.handle_input()

                # Atualiza o estado do jogo
                et = self.clock.tick()  # Tempo entre frames
                keys = pg.key.get_pressed()

                # Verifica se o kart está sobre a textura "pista" ou "borda"
                on_track = self.renderer.is_on_track(self.kart.posx, self.kart.posy)
                on_border = self.renderer.is_on_border(self.kart.posx, self.kart.posy)

                # Atualiza a posição e velocidade do kart considerando se está na pista ou borda
                self.kart.update(keys, et, on_track, on_border)

                # Verifica se cruzou a linha de chegada
                self.check_finish_line()

            # Renderiza o cenário e os sprites
            self.render_game_frame()

            # Atualiza a tela
            pg.display.update()

if __name__ == '__main__':
    Game().run()
    pg.quit()
