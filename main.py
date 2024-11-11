import pygame as pg
import numpy as np
from numba import njit
import random
import serial

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
COINS = 10
TIME = 600000
LAPS = 10

class Kart:
    """Representa o kart do jogador com posição, rotação e mecânicas de movimento."""
    def __init__(self):
        # Posição inicial (x, y) e rotação (em radianos)
        self.posx, self.posy, self.rot = 27, 18.5, 4.7
        self.vel = 0 # Velocidade atual
        # Parâmetros de movimento
        self.acceleration = 0.00001
        self.deceleration = 0.00002
        self.brake_deceleration = 0.00005
        self.max_speed = 0.01
        self.min_speed = -0.005
        self.slow_down_factor = 1
        self.rotation_speed_factor = 0.05

    def handle_movement(self, turn_value, accelerate_value, brake_value):
        """ Atualiza a velocidade e rotação do kart com base nos valores de entrada.
            Parâmetros:
            turn_value (float): Valor indicando a direção e magnitude da curva.
            accelerate_value (float): Valor indicando a entrada de aceleração.
            brake_value (float): Valor indicando a entrada de freio. """
        if self.vel != 0:
            # Calcula a velocidade de rotação baseada na velocidade atual
            speed_ratio = abs(self.vel) / self.max_speed
            rotation_speed = turn_value * self.rotation_speed_factor * speed_ratio
            self.rot += rotation_speed
        # Trata a entrada de aceleração
        if accelerate_value > 0:
            self.vel += self.acceleration * accelerate_value
            self.vel = min(self.vel, self.max_speed)
        # Trata a entrada de freio
        elif brake_value > 0:
            if self.vel > 0:
                self.vel -= self.brake_deceleration * brake_value
                self.vel = max(self.vel, 0)
            else:
                self.vel -= self.acceleration * brake_value
                self.vel = max(self.vel, self.min_speed)
        else:
            # Aplica desaceleração natural quando não há entrada
            if self.vel > 0:
                self.vel = max(self.vel - self.deceleration, 0)
            elif self.vel < 0:
                self.vel = min(self.vel + self.deceleration, 0)
        # Limita a velocidade dentro do intervalo permitido
        self.vel = max(min(self.vel, self.max_speed), self.min_speed)

    def update(self, et, on_track, maph, size):
        """ Atualiza a posição do kart com base na velocidade e verifica colisões com a pista. 
        Parâmetros:
            et (int): Tempo decorrido desde a última atualização em milissegundos.
            on_track (bool): Indica se o kart está atualmente na pista.
            maph (np.ndarray): Layout do mapa como uma matriz 2D.
            size (int): Tamanho do mapa. """
        if not on_track:
            self.vel *= self.slow_down_factor # Reduz a velocidade se estiver fora da pista
        # Calcula a variação de movimento com base na rotação e velocidade
        cos_rot = np.cos(self.rot)
        sin_rot = np.sin(self.rot)
        delta_x = cos_rot * self.vel * et
        delta_y = sin_rot * self.vel * et

        next_posx = self.posx + delta_x
        next_posy = self.posy + delta_y

        can_move_x = True
        can_move_y = True
        # Verifica colisão no eixo X
        map_x, map_y = int(next_posx) % size, int(self.posy) % size
        if maph[map_x][map_y] != 1:
            self.posx = next_posx
        else:
            can_move_x = False
        # Verifica colisão no eixo Y
        map_x, map_y = int(self.posx) % size, int(next_posy) % size
        if maph[map_x][map_y] != 1:
            self.posy = next_posy
        else:
            can_move_y = False
        # Trata a resposta à colisão
        if not can_move_x and not can_move_y:
            self.vel = 0
        elif not can_move_x or not can_move_y:
            sliding_friction = 0.985
            self.vel *= sliding_friction

class Renderer:
    """Responsável por renderizar os gráficos do jogo, incluindo o céu, chão e objetos."""
    def __init__(self, hres, halfvres):
        self.hres, self.halfvres = hres, halfvres
        self.mod = hres / 60
        self.size = 32
        self.maph = np.zeros((self.size, self.size), dtype=int)
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))
        self.load_assets()
        self.create_map_boundaries()

    def create_map_boundaries(self):
        """Cria limites ao redor do mapa para evitar que o kart saia dos limites."""
        self.maph[0, :] = 1
        self.maph[:, 0] = 1
        self.maph[self.size - 1, :] = 1
        self.maph[:, self.size - 1] = 1

    def load_assets(self):
        """Carrega e inicializa todos os recursos gráficos necessários para a renderização."""
        self.sky = self.load_and_scale_image('assets/skybox.jpg', (360, self.halfvres * 2))
        self.floor = self.load_image('assets/MarioKart.png')
        self.track_surface = self.load_image('assets/pista.png', alpha=False)
        self.wall_texture = np.full((100, 100, 3), [0.5, 0.5, 0.5])

    @staticmethod
    def load_image(path, alpha=False):
        """ Carrega uma imagem do caminho fornecido. 
        Parâmetros:
         path (str): Caminho para o arquivo de imagem.
         alpha (bool): Se deve incluir transparência alfa.
        Retorna:
         np.ndarray: A imagem carregada como um array NumPy normalizado."""
        image = pg.image.load(path)
        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
        return pg.surfarray.array3d(image) / 255

    @staticmethod
    def load_and_scale_image(path, size):
        """ Carrega e redimensiona uma imagem para o tamanho especificado.
        Parâmetros:
         path (str): Caminho para o arquivo de imagem.
         size (tuple): Tamanho desejado como (largura, altura).
        Retorna:
         np.ndarray: A imagem carregada e redimensionada como um array NumPy normalizado. """
        image = pg.transform.scale(pg.image.load(path), size)
        return pg.surfarray.array3d(image) / 255

    def render_frame(self, posx, posy, rot):
        """Renderiza um único frame com base na posição e rotação do kart.
        Parâmetros:
         posx (float): Posição x do kart.
         posy (float): Posição y do kart.
         rot (float): Rotação do kart em radianos.
        Retorna:
         pg.Surface: O frame renderizado como uma superfície Pygame."""
        self.frame = new_frame(
            posx, posy, rot, self.frame, self.sky, self.floor,
            self.track_surface, self.hres, self.halfvres, self.mod, self.maph, self.size, self.wall_texture
        )
        return pg.surfarray.make_surface(self.frame * 255)

    def is_on_track(self, posx, posy):
        height, width = self.track_surface.shape[:2]
        xx = int((posx / self.size) * (width - 1))
        yy = int((1 - posy / self.size) * (height - 1))
        xx = np.clip(xx, 0, width - 1)
        yy = np.clip(yy, 0, height - 1)
        red = self.track_surface[yy, xx, 0]
        return red > 0.5

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, hres, halfvres, mod, maph, size, wall_texture):
    """Gera um novo frame para renderização usando código otimizado compilado com Numba.
    Retorna:
     np.ndarray: Buffer do frame atualizado."""
    for i in range(hres):
        # Calcula a rotação para a coluna atual
        rot_i = rot + np.deg2rad(i / mod - 30)
        sin_rot, cos_rot = np.sin(rot_i), np.cos(rot_i)
        cos2 = np.cos(np.deg2rad(i / mod - 30))
        sky_index = int(np.rad2deg(rot_i) % 359)
        frame[i][:] = sky[sky_index][:]  # Define a cor do céu

        for j in range(halfvres):
            # Calcula a distância e posição com base no ângulo atual e j
            n = (halfvres / (halfvres - j)) / cos2
            x = posx + cos_rot * n
            y = posy + sin_rot * n
            xx = int(x / 30 % 1 * 1023)
            yy = int(y / 30 % 1 * 1023)
            shade = 0.95 + 0.05 * (1 - j / halfvres)

            map_x, map_y = int(x) % size, int(y) % size
            if maph[map_x][map_y] == 1:
                # Colisão detectada com parede
                h = halfvres - j
                c = shade * wall_texture[int(x * 10 % 100)][int(y * 10 % 100)]
                min_k = max(0, halfvres - h)
                max_k = min(frame.shape[1], halfvres + h)
                frame[i][min_k:max_k] = c  # Desenha a parede
                break
            else:
                # Desenha o chão
                frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade
    return frame

class SoundManager:
    """Gerencia todos os sons do jogo, incluindo música de fundo e efeitos sonoros."""
    def __init__(self):
        # Carrega e reproduz a música de fundo
        pg.mixer.music.load('assets/nirvana.mp3')
        pg.mixer.music.play(-1) # Loop indefinidamente
        pg.mixer.music.set_volume(0.3)
        # Carrega efeitos sonoros
        self.item_sound = pg.mixer.Sound('assets/item.mp3')
        self.boost_sound = pg.mixer.Sound('assets/boost.mp3')
        self.unboost_sound = pg.mixer.Sound('assets/unboost.mp3')
        self.coin_up_sound = pg.mixer.Sound('assets/coin_up.mp3')
        self.coin_down_sound = pg.mixer.Sound('assets/coin_down.mp3')
        self.victory_sound = pg.mixer.Sound('assets/victory.mp3')
        self.lose_sound = pg.mixer.Sound('assets/lose.mp3')
        # Define o volume para todos os efeitos sonoros
        for sound in [self.item_sound, self.boost_sound, self.unboost_sound,
                      self.coin_up_sound, self.coin_down_sound, self.victory_sound, self.lose_sound]:
            sound.set_volume(0.5)

class Game:
    """Classe principal do jogo que lida com inicialização, loop do jogo, renderização e lógica do jogo."""
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.kart = Kart()
        self.renderer = Renderer(120, 100)
        self.load_sprites()
        self.initialize_game_variables()
        self.initialize_joysticks()
        self.load_assets()
        self.original_max_speed = self.kart.max_speed
        self.original_acceleration = self.kart.acceleration
        # Tenta abrir a porta serial para entrada de sensores
        try:
            self.serial_port = serial.Serial('COM5', 115200, timeout=0)
            self.serial_port.setDTR(False)
            print("Porta serial COM5 aberta com sucesso.")
        except serial.SerialException:
            print("Erro: Não foi possível abrir a porta serial COM5")
            self.serial_port = None
        # Inicializa variáveis dos sensores
        self.sensor_ay = 0
        self.sensor_button1 = 0
        self.sensor_button2 = 0
        self.sensor_button3 = 0
        self.sensor_button4 = 0
        # Configuração dos sensores
        self.sensor_max_angle = 90
        self.sensor_max_value = -15600
        self.turn_sensitivity = 0.8
        self.max_turn_value = 5.0
        # Estados anteriores dos botões dos sensores para detecção de borda
        self.sensor_button3_prev = 0
        self.sensor_button4_prev = 0
        self.power_button_pressed = False
        self.pause_button_pressed = False
        self.paused = False
        self.pause_start_time = None
        self.total_paused_time = 0

    def initialize_game_variables(self):
        """Inicializa ou reseta todas as variáveis relacionadas ao jogo."""
        self.running = True
        self.controls_enabled = False
        self.lap_count = 0
        self.has_crossed_finish_line = False
        self.current_power = None
        self.power_activation_time = None
        self.power_in_use = False
        # Lista de poderes disponíveis
        self.powers = ['Boost', 'Un-Boost', '+ 1 Moeda :)', '- 1 Moeda :(', '- 1 Volta :)', '+ 1 Volta :(']
        self.coin_count = 0
        self.start_time = None
        self.game_over = False
        self.game_over_time = None
        self.game_result = None
        self.restart_game = False

    def initialize_joysticks(self):
        """Inicializa joysticks conectados para entrada no jogo."""
        pg.joystick.init()
        self.joysticks = []
        for i in range(pg.joystick.get_count()):
            joystick = pg.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)

    def load_sprites(self):
        """Carrega e redimensiona todas as imagens de sprites usadas no jogo."""
        # Carrega sprites do Mario a partir da folha de sprites
        mario_sheet = pg.image.load('assets/mario_sheet.png').convert_alpha()
        sprite_width, sprite_height, sprite_scale = 32, 32, 6.5
        positions = [(5.55, 1.1), (4.6, 1.1), (7.38, 1.1)]
        sprites = []
        for x, y in positions:
            # Extrai sprites individuais da folha
            sprite = mario_sheet.subsurface(pg.Rect(x * sprite_width, y * sprite_height, sprite_width, sprite_height))
            # Redimensiona sprites
            sprite = pg.transform.scale(sprite, (int(sprite_width * sprite_scale), int(sprite_height * sprite_scale)))
            sprites.append(sprite)
        self.mario_w, self.mario_a, self.mario_d = sprites
        # Carrega sprite do kart
        self.kart_sprite = pg.transform.scale(pg.image.load('assets/kart.png'), (200, 200))
        self.current_sprite = self.mario_w # Define sprite inicial

    def load_assets(self):
        """Carrega recursos adicionais do jogo, como fontes, sons e imagens."""
        pg.font.init()
        self.font = pg.font.SysFont('Arial', 24)
        self.font_2 = pg.font.SysFont('Arial', 48)
        # Carrega imagens de contagem regressiva
        self.countdown_images = [pg.image.load(f'assets/{i}.png') for i in ['3', '2', '1', 'go']]
        self.countdown_sound = 'assets/ct.mp3'
        # Carrega sprites de caixa e moeda
        self.box_sprite = pg.transform.scale(pg.image.load('assets/box.png').convert_alpha(), (50, 50))
        self.coin_sound = pg.mixer.Sound('assets/moeda.mp3')
        self.coin_sound.set_volume(0.1)
        self.coin_sprite = pg.image.load('assets/moeda.png').convert_alpha()
        self.initialize_game_objects()

    def initialize_game_objects(self):
        """Inicializa objetos do jogo como caixas de itens e moedas com suas posições."""
        self.item_boxes = [
            {'posx': 26.70, 'posy': 14.90, 'active': True, 'respawn_time': None},
            {'posx': 27.41, 'posy': 14.90, 'active': True, 'respawn_time': None},
            {'posx': 28.12, 'posy': 14.90, 'active': True, 'respawn_time': None},
            {'posx': 11.00, 'posy': 4.80, 'active': True, 'respawn_time': None},
            {'posx': 11.27, 'posy': 4.06, 'active': True, 'respawn_time': None},
            {'posx': 11.70, 'posy': 3.32, 'active': True, 'respawn_time': None}
        ]
        self.coins = [
            {'posx': 26.65, 'posy': 13.05},
            {'posx': 20.29, 'posy': 7.30},
            {'posx': 16.50, 'posy': 7.44},
            {'posx': 12.07, 'posy': 3.61},
            {'posx': 3.00, 'posy': 11.2},
            {'posx': 3.00, 'posy': 7.01},
            {'posx': 2.52, 'posy': 17.47},
            {'posx': 9.02, 'posy': 20.24},
            {'posx': 13.52, 'posy': 16.98},
            {'posx': 18.42, 'posy': 21.01},
            {'posx': 23.46, 'posy': 25.68},
            {'posx': 27.38, 'posy': 21.79},
            {'posx': 7.54, 'posy': 19.00},
            {'posx': 28.01, 'posy': 15.48},
            {'posx': 2.52, 'posy': 22.65}
        ]

    def read_sensor_data(self):
        """Lê e analisa os dados dos sensores a partir da porta serial."""
        if self.serial_port:
            try:
                line = self.serial_port.readline().decode('utf-8').rstrip()
                if line:
                    data_parts = line.split(',')
                    for part in data_parts:
                        if part.startswith('ay:'):
                            value_str = part[3:]
                            if value_str.strip():
                                self.sensor_ay = int(value_str)
                        elif part.startswith('button1:'):
                            value_str = part[8:]
                            if value_str.strip():
                                self.sensor_button1 = int(value_str)
                        elif part.startswith('button2:'):
                            value_str = part[8:]
                            if value_str.strip():
                                self.sensor_button2 = int(value_str)
                        elif part.startswith('button3:'):
                            value_str = part[8:]
                            if value_str.strip():
                                self.sensor_button3 = int(value_str)
                        elif part.startswith('button4:'):
                            value_str = part[8:]
                            if value_str.strip():
                                self.sensor_button4 = int(value_str)
            except (UnicodeDecodeError, ValueError) as e:
                print(f"Erro ao analisar os dados seriais: {e}")

    def handle_input(self):
        """Lida com todas as entradas do jogador a partir do teclado, joystick e sensores."""
        keys = pg.key.get_pressed()
        # Calcula o valor de curva com base nas teclas de seta ou WASD
        turn_value = (keys[pg.K_RIGHT] or keys[pg.K_d]) - (keys[pg.K_LEFT] or keys[pg.K_a])
        # Determina os valores de aceleração e freio
        accelerate_value = keys[pg.K_UP] or keys[pg.K_w]
        brake_value = keys[pg.K_DOWN] or keys[pg.K_s]
        # Trata a entrada do joystick se estiver conectado
        if self.joysticks:
            joystick = self.joysticks[0]
            axis_horizontal = joystick.get_axis(0)
            trigger_axis_left = joystick.get_axis(4)
            trigger_axis_right = joystick.get_axis(5)
            deadzone = 0.1

            if abs(axis_horizontal) > deadzone:
                turn_value += axis_horizontal

            left_trigger_value = (trigger_axis_left + 1) / 2
            right_trigger_value = (trigger_axis_right + 1) / 2

            if left_trigger_value > deadzone:
                brake_value = left_trigger_value
            if right_trigger_value > deadzone:
                accelerate_value = right_trigger_value
        # Lê os dados dos sensores da porta serial
        self.read_sensor_data()
        if self.sensor_ay != 0:
            # Normaliza o valor Y do acelerômetro e ajusta o valor de curva
            normalized_ay = self.sensor_ay / self.sensor_max_value
            turn_value += normalized_ay * self.turn_sensitivity
        # Limita o valor de curva dentro do máximo permitido
        turn_value = max(-self.max_turn_value, min(self.max_turn_value, turn_value))
        # Trata as entradas dos botões dos sensores
        if self.sensor_button1 == 1:
            accelerate_value += 1
        if self.sensor_button2 == 1:
            brake_value += 1
        # Detecta borda de subida para o botão de poder
        if self.sensor_button3 == 1 and self.sensor_button3_prev == 0:
            if not self.paused:
                self.power_button_pressed = True
        self.sensor_button3_prev = self.sensor_button3
        # Detecta borda de subida para o botão de pausa
        if self.sensor_button4 == 1 and self.sensor_button4_prev == 0:
            self.pause_button_pressed = True
        self.sensor_button4_prev = self.sensor_button4

        if not self.paused:
            # Atualiza o movimento do kart com base nas entradas
            self.kart.handle_movement(turn_value, accelerate_value, brake_value)
            self.update_current_sprite(turn_value, brake_value)

    def update_current_sprite(self, turn_value, brake_value):
        """Atualiza o sprite atual com base no movimento e ações do kart.
        Parâmetros:
         turn_value (float): Valor indicando a direção e magnitude da curva.
         brake_value (float): Valor indicando a entrada de freio."""
        if self.kart.vel < 0:
            self.current_sprite = self.kart_sprite  # Sprite do kart ao mover para trás
        elif turn_value < -0.1:
            self.current_sprite = self.mario_a  # Sprite virando à esquerda
        elif turn_value > 0.1:
            self.current_sprite = self.mario_d  # Sprite virando à direita
        elif brake_value > 0.1 and self.kart.vel > 0:
            self.current_sprite = self.kart_sprite  # Sprite do kart ao frear
        else:
            self.current_sprite = self.mario_w  # Sprite andando

    def countdown(self):
        """Exibe uma contagem regressiva antes do início do jogo."""
        pg.mixer.music.load(self.countdown_sound)
        pg.mixer.music.play()
        for image in self.countdown_images:
            self.render_game_frame()
            # Centraliza a imagem da contagem regressiva na tela
            self.screen.blit(image, image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
            pg.display.update()
            pg.time.wait(1000) # Aguarda 1 segundo entre as etapas da contagem regressiva
        while pg.mixer.music.get_busy():
            pg.time.wait(100)
        self.sound_manager = SoundManager()
        self.controls_enabled = True

    def check_finish_line(self):
        """Verifica se o kart cruzou a linha de chegada para incrementar a contagem de voltas."""
        finish_line_x_min = 26.25
        finish_line_x_max = 28.7
        finish_line_y = 17.5

        if finish_line_x_min <= self.kart.posx <= finish_line_x_max and abs(self.kart.posy - finish_line_y) < 0.1:
            if self.kart.vel > 0 and not self.has_crossed_finish_line:
                self.lap_count += 1
                self.has_crossed_finish_line = True
        else:
            self.has_crossed_finish_line = False

    def render_game_frame(self):
        """Renderiza todos os elementos do frame do jogo, incluindo a cena e a interface do usuário."""
        camera_offset = -1.0
        # Calcula a posição da câmera com base na posição e rotação do kart
        camera_x = self.kart.posx + np.cos(self.kart.rot) * camera_offset
        camera_y = self.kart.posy + np.sin(self.kart.rot) * camera_offset
        # Renderiza a cena
        frame_surface = self.renderer.render_frame(camera_x, camera_y, self.kart.rot)
        self.draw_objects(frame_surface, camera_x, camera_y)
        # Redimensiona o frame para o tamanho da tela e blita na exibição
        frame_surface = pg.transform.scale(frame_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(frame_surface, (0, 0))
        # Desenha o sprite atual
        self.screen.blit(self.current_sprite, self.current_sprite.get_rect(center=(400, 600 - 120)))
        self.draw_ui()

    def draw_objects(self, frame_surface, camera_x, camera_y):
        """Desenha todos os objetos do jogo, como caixas de itens e moedas, no frame.
        Parâmetros:
         frame_surface (pg.Surface): A superfície do frame atual para desenhar.
         camera_x (float): Posição x da câmera.
         camera_y (float): Posição y da câmera."""
        # Desenha caixas de itens ativas
        self.draw_sprites(frame_surface, self.item_boxes, self.box_sprite, camera_x, camera_y, is_active_key='active')
        # Desenha moedas
        self.draw_sprites(frame_surface, self.coins, self.coin_sprite, camera_x, camera_y)

    def draw_sprites(self, frame_surface, objects, sprite_image, camera_x, camera_y, is_active_key=None):
        """Desenha uma lista de sprites (objetos) no frame com base em suas posições relativas à câmera.
        Parâmetros:
         frame_surface (pg.Surface): A superfície do frame atual para desenhar.
         objects (list): Lista de objetos com posições.
         sprite_image (pg.Surface): A imagem do sprite a ser desenhada.
         camera_x (float): Posição x da câmera.
         camera_y (float): Posição y da câmera.
         is_active_key (str, opcional): Chave para verificar se o objeto está ativo."""
        for obj in objects:
            if is_active_key and not obj.get(is_active_key, True):
                continue  # Pula objetos inativos
            dx = obj['posx'] - camera_x
            dy = obj['posy'] - camera_y
            distance = np.hypot(dx, dy)
            angle_to_obj = np.arctan2(dy, dx)
            angle_difference = (angle_to_obj - self.kart.rot + np.pi) % (2 * np.pi) - np.pi
            # Apenas desenha objetos dentro de um campo de visão de 30 graus
            if abs(angle_difference) < np.deg2rad(30):
                hres = self.renderer.hres
                halfvres = self.renderer.halfvres
                # Calcula a posição horizontal na tela
                screen_x = (angle_difference / np.deg2rad(30)) * (hres / 2) + (hres / 2)
                corrected_distance = max(0.1, distance)
                K = 70
                # Calcula o tamanho do sprite com base na distância
                sprite_height = int(K / corrected_distance)
                sprite_height = np.clip(sprite_height, 5, 200)
                aspect_ratio = (0.5 * sprite_image.get_width()) / sprite_image.get_height()
                sprite_width = int(sprite_height * aspect_ratio)
                # Redimensiona o sprite com base na distância
                sprite = pg.transform.scale(sprite_image, (sprite_width, sprite_height))
                screen_ground_y = halfvres + (halfvres / corrected_distance)
                near_distance = 2
                max_offset = 50
                # Aplica deslocamento vertical para objetos mais próximos
                vertical_offset = max_offset * (1 - (corrected_distance / near_distance)) if corrected_distance < near_distance else 0
                screen_y = screen_ground_y - sprite_height - vertical_offset
                # Verifica se o sprite está dentro dos limites da tela antes de desenhar
                if 0 <= screen_x - sprite_width / 2 <= hres and 0 <= screen_y <= halfvres * 2:
                    frame_surface.blit(sprite, (screen_x - sprite_width / 2, screen_y))

    def draw_ui(self):
        """Desenha os elementos da interface do usuário, como posição, voltas, moedas, poder e tempo."""
        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)
        self.draw_text(f'Moedas: {self.coin_count}', SCREEN_WIDTH - 10, 10, align_right=True)
        power_text = 'Poder: Nenhum' if self.current_power is None else f'Poder: {self.current_power}'
        self.draw_text(power_text, 10, 70)

        if self.start_time is not None:
            # Calcula o tempo decorrido excluindo as durações pausadas
            elapsed_time = self.get_elapsed_time()
            elapsed_seconds = int(elapsed_time)
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            time_str = f'Tempo: {minutes:02}:{seconds:02}'
            self.draw_text(time_str, SCREEN_WIDTH - 10, 40, align_right=True)

    def draw_text(self, text, x, y, align_right=False, font=None, color=(255, 255, 255), border_color=(0, 0, 0)):
        """Renderiza e desenha texto na tela com uma borda opcional para melhor visibilidade."""
        font = font if font else self.font
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(topright=(x, y)) if align_right else text_surface.get_rect(topleft=(x, y))

        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            border_surface = font.render(text, True, border_color)
            border_rect = border_surface.get_rect(center=(text_rect.centerx + dx, text_rect.centery + dy))
            self.screen.blit(border_surface, border_rect)

        self.screen.blit(text_surface, text_rect)

    def check_collisions(self):
        """Verifica colisões entre o kart e moedas ou caixas de itens."""
        self.check_coin_collisions()
        self.check_item_box_collisions()

    def check_coin_collisions(self):
        """Detecta e trata colisões entre o kart e moedas."""
        coins_to_remove = []
        for coin in self.coins:
            if self.is_colliding(self.kart, coin):
                self.coin_sound.play()
                self.coin_count += 1
                coins_to_remove.append(coin)
        # Remove moedas coletadas do jogo
        for coin in coins_to_remove:
            self.coins.remove(coin)

    def check_item_box_collisions(self):
        """Detecta e trata colisões entre o kart e caixas de itens."""
        if self.current_power is None and not self.power_in_use:
            for box in self.item_boxes:
                if box['active'] and self.is_colliding(self.kart, box):
                    box['active'] = False
                    box['respawn_time'] = pg.time.get_ticks() + 10000  # Reaparece após 10 segundos
                    self.sound_manager.item_sound.play()
                    self.current_power = "Press X / R /BOT4"  # Prompt para o jogador ativar o poder
                    break

    @staticmethod
    def is_colliding(obj1, obj2, threshold=0.3):
        """Determina se dois objetos estão colidindo com base em suas posições.
        Parâmetros:
         obj1 (Kart): O primeiro objeto (kart).
         obj2 (dict): O segundo objeto com 'posx' e 'posy'.
         threshold (float, opcional): Distância de limiar para colisão.
        Retorna:
         bool: True se estiverem colidindo, False caso contrário."""
        dx = obj2['posx'] - obj1.posx
        dy = obj2['posy'] - obj1.posy
        distance = np.hypot(dx, dy)
        return distance < threshold

    def activate_power(self):
        """Ativa um poder selecionado aleatoriamente a partir dos poderes disponíveis."""
        self.current_power = random.choice(self.powers)
        self.power_activation_time = pg.time.get_ticks()
        self.power_in_use = True
        # Aplica os efeitos do poder com base no poder selecionado
        if self.current_power == 'Boost':
            self.kart.max_speed = self.original_max_speed * 2
            self.kart.acceleration = self.original_acceleration * 2
            #self.kart.vel = self.kart.max_speed
            self.sound_manager.boost_sound.play()
        elif self.current_power == 'Un-Boost':
            self.kart.max_speed = self.original_max_speed * 0.5
            self.kart.acceleration = self.original_acceleration * 0.5
            self.kart.vel = min(self.kart.vel, self.kart.max_speed)
            self.sound_manager.unboost_sound.play()
        elif self.current_power == '+ 1 Moeda :)':
            self.coin_count += 1
            self.sound_manager.coin_up_sound.play()
        elif self.current_power == '- 1 Moeda :(':
            self.coin_count = max(0, self.coin_count - 1)
            self.sound_manager.coin_down_sound.play()
        elif self.current_power == '- 1 Volta :)':
            self.lap_count = max(0, self.lap_count - 1)
            self.sound_manager.coin_up_sound.play()
        elif self.current_power == '+ 1 Volta :(':
            self.lap_count += 1
            self.sound_manager.coin_down_sound.play()

    def update_powers(self):
        """Atualiza o status dos poderes ativos e reverte as mudanças após o término da duração."""
        if self.power_in_use and pg.time.get_ticks() - self.power_activation_time >= 5000:
            # Reverte velocidade e aceleração se Boost ou Un-Boost estiver ativo
            if self.current_power in ['Boost', 'Un-Boost']:
                self.kart.max_speed = self.original_max_speed
                self.kart.acceleration = self.original_acceleration
                self.kart.vel = min(self.kart.vel, self.kart.max_speed)
            # Limpa o poder atual
            self.current_power = None
            self.power_in_use = False

    def respawn_boxes(self):
        """Reaparece caixas de itens inativas após o tempo de reaparecimento ter decorrido."""
        current_time = pg.time.get_ticks()
        for box in self.item_boxes:
            if not box['active'] and box['respawn_time'] and current_time >= box['respawn_time']:
                box['active'] = True
                box['respawn_time'] = None

    def show_loading_screen(self):
        """Exibe uma tela de carregamento antes do início do jogo."""
        self.screen.fill((0, 0, 0))
        text_surface = self.font_2.render("Carregando...", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)
        pg.display.update()

    def show_victory_screen(self):
        """Exibe a tela de vitória com estatísticas do jogo."""
        background = pg.image.load('assets/fundo.png')
        self.screen.blit(background, (0, 0))
        # Calcula o tempo total em segundos
        total_time = (self.game_over_time - self.start_time) / 1000
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        time_str = f"{minutes} minutos e {seconds} segundos" if minutes > 0 else f"{seconds} segundos"
        # Prepara mensagens de vitória
        message_line1 = f"Parabéns, você coletou as {self.coin_count} moedas"
        message_line2 = f"em {time_str} e em {self.lap_count} voltas!"
        # Renderiza as superfícies de texto
        text_surface1 = self.font_2.render(message_line1, True, (255, 255, 255))
        text_surface2 = self.font_2.render(message_line2, True, (255, 255, 255))
        x_center = SCREEN_WIDTH // 2
        # Obtém os retângulos de texto centralizados na tela
        text_rect1 = text_surface1.get_rect(center=(x_center, SCREEN_HEIGHT // 2 - 120))
        text_rect2 = text_surface2.get_rect(center=(x_center, SCREEN_HEIGHT // 2 - 80))
        # Desenha textos com bordas
        self.draw_text(message_line1, text_rect1.x, text_rect1.y, font=self.font_2)
        self.draw_text(message_line2, text_rect2.x, text_rect2.y, font=self.font_2)
        # Mostra botões para jogar novamente ou sair
        self.show_end_screen_buttons()
        pg.display.update()

    def show_lose_screen(self):
        """Exibe a tela de derrota com estatísticas do jogo."""
        background = pg.image.load('assets/fundo.png')
        self.screen.blit(background, (0, 0))
        # Prepara mensagens de derrota
        message_line1 = "Você perdeu!"
        message_line2 = f"Coletou {self.coin_count} moedas."
        # Renderiza o texto
        self.draw_text(message_line1, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, align_right=False, font=self.font_2)
        self.draw_text(message_line2, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, align_right=False, font=self.font_2)
        # Mostra botões para jogar novamente ou sair
        self.show_end_screen_buttons()
        pg.display.update()

    def show_end_screen_buttons(self):
        """Exibe os botões de jogar e sair na tela final."""
        play_button = pg.transform.scale(pg.image.load('assets/play.png'), (200, 80))
        exit_button = pg.transform.scale(pg.image.load('assets/exit.png'), (200, 80))
        # Posiciona os botões na tela
        play_button_rect = play_button.get_rect(center=(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
        exit_button_rect = exit_button.get_rect(center=(SCREEN_WIDTH // 2 + 110, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(play_button, play_button_rect)
        self.screen.blit(exit_button, exit_button_rect)
        # Armazena os retângulos dos botões para detecção de cliques
        self.end_screen_play_button_rect = play_button_rect
        self.end_screen_exit_button_rect = exit_button_rect

    def wait_for_menu_selection(self):
        """Aguarda o jogador selecionar uma opção na tela final."""
        waiting = True
        while waiting:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    mouse_pos = pg.mouse.get_pos()
                    # Verifica se o botão de jogar foi clicado
                    if self.end_screen_play_button_rect.collidepoint(mouse_pos):
                        waiting = False
                        self.running = False
                        self.restart_game = True
                    # Verifica se o botão de sair foi clicado
                    elif self.end_screen_exit_button_rect.collidepoint(mouse_pos):
                        waiting = False
                        self.running = False
            pg.time.wait(100)

    def display_pause_message(self):
        """Exibe uma mensagem piscante de pausa quando o jogo está pausado."""
        time_now = pg.time.get_ticks()
        if (time_now // 500) % 2 == 0:
            text_surface = self.font_2.render('Jogo Pausado!', True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text_surface, text_rect)

    def get_elapsed_time(self):
        """Calcula o tempo total decorrido do jogo excluindo as durações pausadas."""
        current_time = pg.time.get_ticks()
        paused_duration = 0
        if self.paused and self.pause_start_time is not None:
            paused_duration = current_time - self.pause_start_time
        elapsed_time_ms = current_time - self.start_time - self.total_paused_time - paused_duration
        return elapsed_time_ms / 1000

    def run(self):
        """Loop principal do jogo que lida com eventos, atualizações e renderização."""
        self.show_loading_screen()
        pg.time.wait(2000)  # Aguarda 2 segundos na tela de carregamento
        self.countdown()
        # Inicializa variáveis de tempo
        self.start_time = pg.time.get_ticks()
        self.pause_start_time = None
        self.total_paused_time = 0

        while self.running:
            et = self.clock.tick(60)  # Limita a taxa de quadros a 60 FPS
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:
                        if not self.paused:
                            self.power_button_pressed = True
                    elif event.key == pg.K_p:
                        self.pause_button_pressed = True
                elif event.type == pg.JOYBUTTONDOWN:
                    if event.button == 2:
                        if not self.paused:
                            self.power_button_pressed = True
                    elif event.button == 3:
                        self.pause_button_pressed = True

            self.handle_input()
            # Trata o pressionamento do botão de pausa
            if self.pause_button_pressed:
                if not self.paused:
                    self.paused = True
                    self.pause_start_time = pg.time.get_ticks()
                else:
                    self.paused = False
                    if self.pause_start_time is not None:
                        paused_duration = pg.time.get_ticks() - self.pause_start_time
                        self.total_paused_time += paused_duration
                        self.pause_start_time = None
                self.pause_button_pressed = False

            if self.paused:
                # Renderiza o frame e exibe a mensagem de pausa
                self.render_game_frame()
                self.display_pause_message()
                pg.display.update()
            else:
                if self.controls_enabled:
                    # Ativa poder se o botão for pressionado e as condições forem atendidas
                    if self.power_button_pressed and self.current_power == "Press X / R" and not self.power_in_use:
                        self.activate_power()
                    # Verifica se o kart está na pista e atualiza a posição
                    on_track = self.renderer.is_on_track(self.kart.posx, self.kart.posy)
                    self.kart.update(et, on_track, self.renderer.maph, self.renderer.size)
                    self.check_finish_line()
                    self.check_collisions()
                    self.update_powers()
                    self.respawn_boxes()
                # Calcula o tempo decorrido
                elapsed_time = self.get_elapsed_time()

                if not self.game_over:
                    # Determina se o jogo foi ganho ou perdido com base nas condições
                    if self.coin_count >= COINS and elapsed_time <= TIME and self.lap_count <= LAPS:
                        self.game_over = True
                        self.game_over_time = pg.time.get_ticks()
                        self.game_result = 'win'
                        pg.mixer.music.stop()
                        self.sound_manager.victory_sound.play()
                    elif elapsed_time > TIME or self.lap_count >= LAPS:
                        self.game_over = True
                        self.game_over_time = pg.time.get_ticks()
                        self.game_result = 'lose'
                        pg.mixer.music.stop()
                        self.sound_manager.lose_sound.play()

                if self.game_over:
                    # Aguarda 3 segundos antes de mostrar a tela final
                    if pg.time.get_ticks() - self.game_over_time >= 3000:
                        if self.game_result == 'win':
                            self.show_victory_screen()
                        else:
                            self.show_lose_screen()
                        self.wait_for_menu_selection()
                        self.running = False
                        break
                # Renderiza o frame atual do jogo e atualiza a exibição
                self.render_game_frame()
                pg.display.update()

            self.power_button_pressed = False  # Reseta o estado do botão de poder
        # Fecha a porta serial se estiver aberta
        if self.serial_port:
            self.serial_port.close()

def menu():
    """Exibe o menu principal e lida com as interações do menu."""
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("Menu")
    # Carrega fundo e botões do menu
    background = pg.image.load('assets/fundo.png')
    play_button = pg.transform.scale(pg.image.load('assets/play.png'), (200, 80))
    exit_button = pg.transform.scale(pg.image.load('assets/exit.png'), (200, 80))
    # Posiciona os botões na tela
    play_button_rect = play_button.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    exit_button_rect = exit_button.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

    running = True
    while running:
        screen.blit(background, (0, 0))
        screen.blit(play_button, play_button_rect)
        screen.blit(exit_button, exit_button_rect)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                if play_button_rect.collidepoint(mouse_pos):
                    # Inicia o jogo quando o botão de jogar é clicado
                    game = Game()
                    game.run()
                    if game.restart_game:
                        continue  # Reinicia o menu se necessário
                    else:
                        running = False
                elif exit_button_rect.collidepoint(mouse_pos):
                    running = False

        pg.display.update()

if __name__ == '__main__':
    menu()
    pg.quit()