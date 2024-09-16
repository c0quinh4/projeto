import pygame as pg
from kart import Kart
from renderer import Renderer
from sound_manager import SoundManager

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((800, 600))
        self.clock = pg.time.Clock()
        self.kart = Kart()
        self.renderer = Renderer(120, 100)
        self.sound_manager = SoundManager()
        self.load_sprites()
        self.running = True
        self.controls_enabled = False  # Controles inicialmente desativados
        self.lap_count = 0
        self.has_crossed_finish_line = False

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
        self.countdown_sound = 'assets/ct.mp3'

    def load_sprites(self):
        mario_sheet = pg.image.load('assets/mario_sheet.png').convert_alpha()
        sprite_width, sprite_height, sprite_scale = 32, 32, 6.5
        self.mario_w = pg.transform.scale(mario_sheet.subsurface(pg.Rect(5.55 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
                                          (sprite_width * sprite_scale, sprite_height * sprite_scale))
        self.mario_a = pg.transform.scale(mario_sheet.subsurface(pg.Rect(4.6 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
                                          (sprite_width * sprite_scale, sprite_height * sprite_scale))
        self.mario_d = pg.transform.scale(mario_sheet.subsurface(pg.Rect(7.38 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
                                          (sprite_width * sprite_scale, sprite_height * sprite_scale))
        self.kart_sprite = pg.transform.scale(pg.image.load('assets/kart.png'), (200, 200))
        self.current_sprite = self.mario_w

    def handle_input(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[ord('a')]:
            self.current_sprite = self.mario_a
        elif keys[pg.K_RIGHT] or keys[ord('d')]:
            self.current_sprite = self.mario_d
        elif keys[pg.K_DOWN] or keys[ord('s')]:
            self.current_sprite = self.kart_sprite
        else:
            self.current_sprite = self.mario_w

    def countdown(self):
        pg.mixer.music.load(self.countdown_sound)
        pg.mixer.music.play()
        for i in range(4):
            self.render_game_frame()
            self.screen.blit(self.countdown_images[i], (400 - self.countdown_images[i].get_width() // 2, 300 - self.countdown_images[i].get_height() // 2))
            pg.display.update()
            pg.time.wait(1000)

        while pg.mixer.music.get_busy():
            pg.time.wait(100)
        self.sound_manager = SoundManager()
        self.controls_enabled = True

    def check_finish_line(self):
        finish_line_x_min = 26.25
        finish_line_x_max = 28.7
        finish_line_y = 17.5

        if finish_line_x_min <= self.kart.posx <= finish_line_x_max and abs(self.kart.posy - finish_line_y) < 0.1:
            if self.kart.vel > 0:
                if not self.has_crossed_finish_line:
                    self.lap_count += 1
                    self.has_crossed_finish_line = True
            else:
                self.has_crossed_finish_line = False
        else:
            self.has_crossed_finish_line = False

    def render_game_frame(self):
        et = self.clock.tick()
        frame_surface = self.renderer.render_frame(self.kart.posx, self.kart.posy, self.kart.rot)
        frame_surface = pg.transform.scale(frame_surface, (800, 600))
        self.screen.blit(frame_surface, (0, 0))
        sprite_rect = self.current_sprite.get_rect(center=(400, 600 - 120))
        self.screen.blit(self.current_sprite, sprite_rect)
        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)

    def draw_text(self, text, x, y):
        text_surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (x, y))

    def show_loading_screen(self):
        """Exibe uma tela de carregamento enquanto os recursos do jogo são preparados."""
        self.screen.fill((0, 0, 0))  # Tela preta
        font = pg.font.SysFont('Arial', 48)
        text_surface = font.render("Carregando...", True, (255, 255, 255))  # Texto branco
        text_rect = text_surface.get_rect(center=(400, 300))
        self.screen.blit(text_surface, text_rect)
        pg.display.update()

    def run(self):
        # Exibe a tela de carregamento antes de começar o jogo
        self.show_loading_screen()

        # Simula o carregamento de recursos (aqui está sendo feito instantaneamente, mas pode levar tempo)
        pg.time.wait(2000)  # Simulando tempo de carregamento de 2 segundos (opcional)

        # Após carregar tudo, inicia o countdown
        self.countdown()

        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.running = False
            if self.controls_enabled:
                self.handle_input()
                et = self.clock.tick()
                keys = pg.key.get_pressed()
                on_track = self.renderer.is_on_track(self.kart.posx, self.kart.posy)
                on_border = self.renderer.is_on_border(self.kart.posx, self.kart.posy)
                self.kart.update(keys, et, on_track, on_border)
                self.check_finish_line()
            self.render_game_frame()
            pg.display.update()
