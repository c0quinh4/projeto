import pygame as pg
import numpy as np
from numba import njit  # Importa o decorador njit para otimização de funções numéricas

class Kart:
    def __init__(self):
        # Inicializa a posição (posx, posy), rotação (rot) e velocidade (vel) do kart
        self.posx, self.posy, self.rot, self.vel = 27, 18.5, 4.7, 0  # Posição inicial
        # Parâmetros de movimento
        self.acceleration = 0.00001          # Taxa de aceleração ao acelerar
        self.deceleration = 0.00001          # Taxa de desaceleração natural
        self.brake_deceleration = 0.00005    # Taxa de desaceleração ao frear
        self.max_speed = 0.01                # Velocidade máxima para frente
        self.min_speed = -0.005              # Velocidade máxima para trás (marcha à ré)
        self.slow_down_factor = 0.99         # Fator de redução de velocidade fora da pista

    def handle_movement(self, turn_value, accelerate_value, brake_value):
        """Processa os inputs de movimento e ajusta a velocidade e direção do kart."""
        # Define o fator de velocidade de rotação
        rotation_speed_factor = 0.008  # Ajuste este valor para controlar a sensibilidade

        # A rotação só ocorre se o kart estiver em movimento
        if self.vel != 0:
            self.rot += turn_value * rotation_speed_factor

        # Aceleração proporcional
        if accelerate_value > 0:
            self.vel += self.acceleration * accelerate_value
            self.vel = min(self.vel, self.max_speed)
        elif brake_value > 0:
            if self.vel > 0:
                # Frenagem proporcional
                self.vel -= self.brake_deceleration * brake_value
                self.vel = max(self.vel, 0)
            elif self.vel == 0:
                # Inicia a marcha à ré
                self.vel -= self.acceleration * brake_value
                self.vel = max(self.vel, self.min_speed)
            elif self.vel < 0:
                # Aumenta a velocidade em marcha à ré
                self.vel -= self.acceleration * brake_value
                self.vel = max(self.vel, self.min_speed)
        else:
            # Desaceleração natural
            if self.vel > 0:
                self.vel = max(self.vel - self.deceleration, 0)
            elif self.vel < 0:
                self.vel = min(self.vel + self.deceleration, 0)

    def update(self, et, on_track, on_border, maph, size):
        """Atualiza a posição do kart com base no tempo e verifica colisões com as paredes."""
        # Se o kart ESTIVER na pista, não aplica redução de velocidade
        if on_track:
            self.vel *= self.slow_down_factor

        # Calcula a nova posição do kart com base na velocidade e direção
        next_posx = self.posx + np.cos(self.rot) * self.vel * et
        next_posy = self.posy + np.sin(self.rot) * self.vel * et

        # Checar colisão com as paredes
        if maph[int(next_posx) % size][int(next_posy) % size] != 1:
            # Se não houver parede, atualiza a posição
            self.posx = next_posx
            self.posy = next_posy
        else:
            # Se houver parede, para o kart
            self.vel = 0

class Renderer:
    def __init__(self, hres, halfvres):
        self.hres, self.halfvres = hres, halfvres
        self.mod = hres / 60
        self.size = 32
        self.maph = np.zeros((self.size, self.size), dtype=int)
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))
        self.load_assets()

        # Define as bordas do mapa como paredes
        self.maph[0, :] = 1
        self.maph[:, 0] = 1
        self.maph[self.size - 1, :] = 1
        self.maph[:, self.size - 1] = 1

    def load_assets(self):
        # Carrega e escala a imagem do céu, convertendo-a em um array
        self.sky = pg.surfarray.array3d(
            pg.transform.scale(
                pg.image.load('assets/skybox.jpg'),
                (360, self.halfvres * 2)
            )
        ) / 255

        # Carrega a textura do chão (pista), convertendo-a em um array
        self.floor = pg.surfarray.array3d(
            pg.image.load('assets/MarioKart.png')
        ) / 255

        # Carrega a máscara que define onde é pista e onde não é
        self.track_surface = pg.surfarray.array3d(
            pg.image.load('assets/pista.png').convert_alpha()
        ) / 255

        # Carrega a máscara que define as bordas da pista
        self.border_surface = pg.surfarray.array3d(
            pg.image.load('assets/borda.png').convert_alpha()
        ) / 255

        # Carrega a textura azul para as paredes
        blue_texture = np.zeros((100, 100, 3))
        blue_texture[:, :] = [0, 0, 1]
        self.wall_texture = blue_texture

    def render_frame(self, posx, posy, rot):
        """Gera um novo frame com base na posição e rotação do kart."""
        self.frame = new_frame(
            posx, posy, rot, self.frame, self.sky, self.floor,
            self.track_surface, self.border_surface,
            self.hres, self.halfvres, self.mod, self.maph, self.size, self.wall_texture
        )
        return pg.surfarray.make_surface(self.frame * 255)

    def is_on_track(self, posx, posy):
        """Verifica se o kart está na pista."""
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        return np.mean(self.track_surface[xx][yy]) > 0.5

    def is_on_border(self, posx, posy):
        """Verifica se o kart está na borda da pista."""
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        if (yy < 5 or yy > 973) or (xx < 5 or xx > 973):
            return True
        return False

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, border_surface, hres, halfvres, mod, maph, size, wall_texture):
    """Função de renderização que gera um novo frame de uma cena em 3D simplificada, utilizando raycasting."""
    for i in range(hres):
        rot_i = rot + np.deg2rad(i / mod - 30)
        sin, cos = np.sin(rot_i), np.cos(rot_i)
        cos2 = np.cos(np.deg2rad(i / mod - 30))
        frame[i][:] = sky[int(np.rad2deg(rot_i) % 359)][:]

        for j in range(halfvres):
            n = (halfvres / (halfvres - j)) / cos2
            x = posx + cos * n
            y = posy + sin * n
            xx = int(x / 30 % 1 * 1023)
            yy = int(y / 30 % 1 * 1023)
            shade = 0.95 + 0.05 * (1 - j / halfvres)

            # Verificar se há uma parede no mapa
            if maph[int(x) % size][int(y) % size] == 1:
                # Renderizar a parede
                h = halfvres - j
                c = shade * wall_texture[int(x * 10 % 100)][int(y * 10 % 100)]
                for k in range(h * 2):
                    if 0 <= halfvres - h + k < frame.shape[1]:
                        frame[i][halfvres - h + k] = c
                break
            else:
                frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade

    return frame

class SoundManager:
    def __init__(self):
        # Gerencia a música de fundo
        pg.mixer.music.load('assets/nirvana.mp3')
        pg.mixer.music.play(-1)
        pg.mixer.music.set_volume(0.3)  # Ajuste o volume conforme necessário

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
        self.controls_enabled = False
        self.lap_count = 0
        self.has_crossed_finish_line = False

        pg.font.init()
        self.font = pg.font.SysFont('Arial', 24)

        # Carrega as imagens e o som usados no countdown
        self.countdown_images = [
            pg.image.load('assets/3.png'),
            pg.image.load('assets/2.png'),
            pg.image.load('assets/1.png'),
            pg.image.load('assets/go.png')
        ]
        self.countdown_sound = 'assets/ct.mp3'

        # Inicializa o módulo de joystick
        pg.joystick.init()

        self.joysticks = []
        for i in range(pg.joystick.get_count()):
            joystick = pg.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)

        # Inicializa as caixas de itens
        self.item_boxes = [{'posx': 27.35, 'posy': 15.62}]
        self.box_sprite = pg.image.load('assets/box.png').convert_alpha()
        # Ajuste o tamanho do sprite conforme necessário
        self.box_sprite = pg.transform.scale(self.box_sprite, (50, 50))  # Exemplo de escala

    def load_sprites(self):
        """Carrega e prepara os sprites usados no jogo."""
        mario_sheet = pg.image.load('assets/mario_sheet.png').convert_alpha()
        sprite_width, sprite_height, sprite_scale = 32, 32, 6.5
        self.mario_w = pg.transform.scale(
            mario_sheet.subsurface(pg.Rect(5.55 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
            (sprite_width * sprite_scale, sprite_height * sprite_scale)
        )
        self.mario_a = pg.transform.scale(
            mario_sheet.subsurface(pg.Rect(4.6 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
            (sprite_width * sprite_scale, sprite_height * sprite_scale)
        )
        self.mario_d = pg.transform.scale(
            mario_sheet.subsurface(pg.Rect(7.38 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
            (sprite_width * sprite_scale, sprite_height * sprite_scale)
        )
        self.kart_sprite = pg.transform.scale(pg.image.load('assets/kart.png'), (200, 200))
        self.current_sprite = self.mario_w

    def handle_input(self):
        """Captura o estado atual das teclas pressionadas e mapeia para valores de direção."""
        keys = pg.key.get_pressed()
        turn_value = 0.0
        accelerate_value = 0.0
        brake_value = 0.0

        # Atualiza o valor da direção
        if keys[pg.K_LEFT] or keys[ord('a')]:
            turn_value = -1.0
        if keys[pg.K_RIGHT] or keys[ord('d')]:
            turn_value = 1.0

        if keys[pg.K_UP] or keys[ord('w')]:
            accelerate_value = 1.0
        if keys[pg.K_DOWN] or keys[ord('s')]:
            brake_value = 1.0

        # Verifica se há joysticks conectados
        if self.joysticks:
            for joystick in self.joysticks:
                # Eixo horizontal (esquerda/direita)
                axis_horizontal = joystick.get_axis(0)

                # Eixo do gatilho
                trigger_axis_left = joystick.get_axis(4)
                trigger_axis_right = joystick.get_axis(5)

                # Zona morta
                deadzone = 0.1

                # Atualiza o valor de virada com base no eixo horizontal
                if abs(axis_horizontal) > deadzone:
                    turn_value = axis_horizontal  # Valor entre -1.0 e 1.0

                # Normaliza os valores dos gatilhos
                left_trigger_value = (trigger_axis_left + 1) / 2
                right_trigger_value = (trigger_axis_right + 1) / 2

                # Mapeia os gatilhos para acelerar e frear
                if left_trigger_value > deadzone:
                    brake_value = left_trigger_value
                else:
                    brake_value = 0.0

                if right_trigger_value > deadzone:
                    accelerate_value = right_trigger_value
                else:
                    accelerate_value = 0.0

        # Atualiza o estado do kart
        self.kart.handle_movement(turn_value, accelerate_value, brake_value)

        # Atualiza o sprite atual com base no estado do kart
        if self.kart.vel < 0:
            self.current_sprite = self.kart_sprite
        elif turn_value < -0.1:
            self.current_sprite = self.mario_a
        elif turn_value > 0.1:
            self.current_sprite = self.mario_d
        elif brake_value > 0.1 and self.kart.vel > 0:
            self.current_sprite = self.kart_sprite
        else:
            self.current_sprite = self.mario_w

    def countdown(self):
        """Executa a contagem regressiva antes do início do jogo."""
        pg.mixer.music.load(self.countdown_sound)
        pg.mixer.music.play()
        for i in range(4):
            # Renderiza o quadro do jogo (fundo, pista, etc.)
            self.render_game_frame()
            self.screen.blit(
                self.countdown_images[i],
                (400 - self.countdown_images[i].get_width() // 2, 300 - self.countdown_images[i].get_height() // 2)
            )
            pg.display.update()
            pg.time.wait(1000)
        while pg.mixer.music.get_busy():
            pg.time.wait(100)
        self.sound_manager = SoundManager()
        self.controls_enabled = True

    def check_finish_line(self):
        """Verifica se o kart cruzou a linha de chegada e atualiza o contador de voltas."""
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
        """Usa o Renderer para renderizar a pista com base na posição e rotação do kart."""
        et = self.clock.tick()
        frame_surface = self.renderer.render_frame(self.kart.posx, self.kart.posy, self.kart.rot)
        # Desenha as caixas de itens
        self.draw_item_boxes(frame_surface)
        frame_surface = pg.transform.scale(frame_surface, (800, 600))
        self.screen.blit(frame_surface, (0, 0))

        sprite_rect = self.current_sprite.get_rect(center=(400, 600 - 120))
        self.screen.blit(self.current_sprite, sprite_rect)

        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)

    def draw_item_boxes(self, frame_surface):
        """Desenha as caixas de itens na tela com tamanho limitado e perspectiva ajustada."""
        for box in self.item_boxes:
            # Calcula a diferença de posição
            dx = box['posx'] - self.kart.posx
            dy = box['posy'] - self.kart.posy
            distance = np.hypot(dx, dy)
            
            # Calcula o ângulo para a caixa e a diferença em relação à rotação do jogador
            angle_to_box = np.arctan2(dy, dx)
            angle_difference = angle_to_box - self.kart.rot
            # Normaliza o ângulo para [-pi, pi]
            angle_difference = (angle_difference + np.pi) % (2 * np.pi) - np.pi
            
            # Campo de visão é +/- 30 graus
            if abs(angle_difference) < np.deg2rad(30):
                # Computa a posição na tela
                hres = self.renderer.hres
                halfvres = self.renderer.halfvres
                screen_x = (angle_difference / np.deg2rad(30)) * (hres / 2) + (hres / 2)
                
                # Usa a distância direta para o cálculo da escala
                corrected_distance = max(0.1, distance)  # Evita divisão por zero
                
                # Calcula o tamanho do sprite usando a constante K
                K = 70  # Ajuste este valor para controlar a escala
                sprite_height = int(K / corrected_distance)
                
                # Define limites para o tamanho do sprite
                max_sprite_height = 200  # Altura máxima do sprite
                min_sprite_height = 5    # Altura mínima do sprite
                sprite_height = min(max_sprite_height, max(min_sprite_height, sprite_height))
                
                # Mantém a proporção do sprite ao calcular a largura
                aspect_ratio = (0.5 * self.box_sprite.get_width()) / self.box_sprite.get_height()
                sprite_width = int(sprite_height * aspect_ratio)
                
                # Redimensiona o sprite mantendo a proporção
                sprite = pg.transform.scale(self.box_sprite, (sprite_width, sprite_height))
                
                # Calcula a linha do chão com base na perspectiva
                screen_ground_y = halfvres + (halfvres / corrected_distance)
                
                # Calcula o deslocamento vertical baseado na distância
                # Quando o jogador está muito próximo, o offset é máximo; quando distante, é zero
                near_distance = 2  # Ajuste este valor conforme necessário
                max_offset = 50      # Deslocamento vertical máximo em pixels
                if corrected_distance < near_distance:
                    vertical_offset = max_offset * (1 - (corrected_distance / near_distance))
                else:
                    vertical_offset = 0
                
                # Posiciona o sprite de modo que a base alinhe com o chão e aplica o deslocamento vertical
                screen_y = screen_ground_y - sprite_height - vertical_offset
                
                # Desenha o sprite se estiver dentro dos limites da tela
                if 0 <= screen_x - sprite_width / 2 <= hres and 0 <= screen_y <= halfvres * 2:
                    frame_surface.blit(sprite, (screen_x - sprite_width / 2, screen_y))

    def draw_text(self, text, x, y):
        """Desenha texto na tela."""
        text_surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (x, y))

    def show_loading_screen(self):
        """Tela de carregamento enquanto os recursos do jogo são preparados."""
        self.screen.fill((0, 0, 0))
        font = pg.font.SysFont('Arial', 48)
        text_surface = font.render("Carregando...", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(400, 300))
        self.screen.blit(text_surface, text_rect)
        pg.display.update()

    def run(self):
        """Método principal que inicia o loop do jogo."""
        # Exibe a tela de carregamento antes de começar o jogo
        self.show_loading_screen()
        pg.time.wait(2000)  # Aguarda 2 segundos

        # Inicia o countdown
        self.countdown()

        # Loop principal do jogo
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.running = False
            # Se os controles estiverem habilitados (após o countdown)
            if self.controls_enabled:
                self.handle_input()
                et = self.clock.tick()
                on_track = self.renderer.is_on_track(self.kart.posx, self.kart.posy)
                on_border = self.renderer.is_on_border(self.kart.posx, self.kart.posy)
                self.kart.update(et, on_track, on_border, self.renderer.maph, self.renderer.size)
                self.check_finish_line()

            self.render_game_frame()
            pg.display.update()

def menu():
    """Exibe a tela de menu principal."""
    pg.init()
    screen_width, screen_height = 800, 600
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("Menu")

    # Carrega os assets (imagens) necessários para o menu
    background = pg.image.load('assets/fundo.png')      # Imagem de fundo do menu
    play_button = pg.image.load('assets/play.png')      # Imagem do botão "Play"
    exit_button = pg.image.load('assets/exit.png')      # Imagem do botão "Exit"

    # Escala os botões
    play_button = pg.transform.scale(play_button, (200, 80))
    exit_button = pg.transform.scale(exit_button, (200, 80))

    # Define as posições dos botões (centralizados na tela)
    button_spacing = 20  # Espaçamento vertical entre os botões
    play_button_rect = play_button.get_rect(
        center=(
            screen_width // 2,
            screen_height // 2 - (exit_button.get_height() // 2 + button_spacing)
        )
    )
    exit_button_rect = exit_button.get_rect(
        center=(
            screen_width // 2,
            screen_height // 2 + (play_button.get_height() // 2 + button_spacing)
        )
    )

    running = True
    while running:
        screen.blit(background, (0, 0))
        screen.blit(play_button, play_button_rect)
        screen.blit(exit_button, exit_button_rect)

        # Captura eventos do Pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                if play_button_rect.collidepoint(mouse_pos):
                    Game().run()  # Inicia o jogo chamando o método run da classe Game
                if exit_button_rect.collidepoint(mouse_pos):
                    running = False

        pg.display.update()

if __name__ == '__main__':
    menu()
    pg.quit()
