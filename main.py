import pygame as pg
import numpy as np
from numba import njit
import random
import serial

# Definição de constantes para largura e altura da tela
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

class Kart:
    def __init__(self):
        # Inicializa a posição, rotação e velocidade do kart
        self.posx, self.posy, self.rot = 27, 18.5, 4.7
        self.vel = 0

        # Parâmetros de movimento
        self.acceleration = 0.00001           # Taxa de aceleração
        self.deceleration = 0.00002           # Taxa de desaceleração natural
        self.brake_deceleration = 0.00005     # Taxa de desaceleração ao frear
        self.max_speed = 0.01                 # Velocidade máxima para frente
        self.min_speed = -0.005               # Velocidade máxima para trás (marcha à ré)
        self.slow_down_factor = 1         # Fator de redução de velocidade na pista

    def handle_movement(self, turn_value, accelerate_value, brake_value):
        """Processa os inputs de movimento e ajusta a velocidade e direção do kart."""
        rotation_speed_factor = 0.01  # Fator de velocidade de rotação

        if self.vel != 0:
            # Ajusta a rotação do kart com base na velocidade atual
            speed_ratio = abs(self.vel) / self.max_speed
            rotation_speed = turn_value * rotation_speed_factor * speed_ratio
            self.rot += rotation_speed

        # Aceleração
        if accelerate_value > 0:
            self.vel += self.acceleration * accelerate_value
            self.vel = min(self.vel, self.max_speed)
        # Frenagem
        elif brake_value > 0:
            if self.vel > 0:
                self.vel -= self.brake_deceleration * brake_value
                self.vel = max(self.vel, 0)
            elif self.vel == 0:
                self.vel -= self.acceleration * brake_value
                self.vel = max(self.vel, self.min_speed)
            elif self.vel < 0:
                self.vel -= self.acceleration * brake_value
                self.vel = max(self.vel, self.min_speed)
        # Desaceleração natural
        else:
            if self.vel > 0:
                self.vel = max(self.vel - self.deceleration, 0)
            elif self.vel < 0:
                self.vel = min(self.vel + self.deceleration, 0)

    def update(self, et, on_track, maph, size):
        """Atualiza a posição do kart com base no tempo e verifica colisões."""
        # Aplica o fator de redução de velocidade se o kart estiver fora da pista
        if not on_track:
            self.vel *= self.slow_down_factor

        # Calcula os deltas de posição
        cos_rot = np.cos(self.rot)
        sin_rot = np.sin(self.rot)
        delta_x = cos_rot * self.vel * et
        delta_y = sin_rot * self.vel * et

        # Próximas posições potenciais
        next_posx = self.posx + delta_x
        next_posy = self.posy + delta_y

        # Flags para verificar se o movimento é possível em cada eixo
        can_move_x = True
        can_move_y = True

        # Checa colisão no eixo x
        map_x, map_y = int(next_posx) % size, int(self.posy) % size
        if maph[map_x][map_y] != 1:
            self.posx = next_posx
        else:
            can_move_x = False

        # Checa colisão no eixo y
        map_x, map_y = int(self.posx) % size, int(next_posy) % size
        if maph[map_x][map_y] != 1:
            self.posy = next_posy
        else:
            can_move_y = False

        # Se não puder se mover em nenhum eixo, para o kart
        if not can_move_x and not can_move_y:
            self.vel = 0
        # Se estiver deslizando na parede (colidiu em um eixo, mas não no outro), diminui a velocidade
        elif not can_move_x or not can_move_y:
            # Aplica uma desaceleração
            sliding_friction = 0.985  # Fator de redução de velocidade ao deslizar (20% de redução)
            self.vel *= sliding_friction

class Renderer:
    def __init__(self, hres, halfvres):
        # Inicializa as resoluções horizontal e vertical
        self.hres, self.halfvres = hres, halfvres
        self.mod = hres / 60  # Fator de modulação para o ângulo de visão
        self.size = 32  # Tamanho do mapa
        self.maph = np.zeros((self.size, self.size), dtype=int)  # Mapa das paredes
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))  # Frame inicial
        self.load_assets()
        self.create_map_boundaries()

    def create_map_boundaries(self):
        """Cria as bordas do mapa como paredes."""
        self.maph[0, :] = 1
        self.maph[:, 0] = 1
        self.maph[self.size - 1, :] = 1
        self.maph[:, self.size - 1] = 1

    def load_assets(self):
        """Carrega os recursos necessários para renderização."""
        self.sky = self.load_and_scale_image('assets/skybox.jpg', (360, self.halfvres * 2))
        self.floor = self.load_image('assets/MarioKart.png')
        self.track_surface = self.load_image('assets/pista.png', alpha=True)
        self.border_surface = self.load_image('assets/borda.png', alpha=True)
        self.externos_surface = self.load_image('assets/externo.png', alpha=True)
        self.wall_texture = np.full((100, 100, 3), [0, 0, 1])  # Textura azul para as paredes

    @staticmethod
    def load_image(path, alpha=False):
        """Carrega uma imagem e a converte para um array numpy."""
        image = pg.image.load(path)
        if alpha:
            image = image.convert_alpha()
            array = pg.surfarray.pixels_alpha(image) / 255
            array_rgb = pg.surfarray.array3d(image) / 255
            # Adiciona o canal alfa como a quarta dimensão
            array_rgba = np.dstack((array_rgb, array))
            return array_rgba
        else:
            image = image.convert()
            return pg.surfarray.array3d(image) / 255

    @staticmethod
    def load_and_scale_image(path, size):
        """Carrega e escala uma imagem."""
        image = pg.transform.scale(pg.image.load(path), size)
        return pg.surfarray.array3d(image) / 255

    def render_frame(self, posx, posy, rot):
        """Gera um novo frame com base na posição e rotação do kart."""
        self.frame = new_frame(
            posx, posy, rot, self.frame, self.sky, self.floor,
            self.track_surface, self.hres, self.halfvres, self.mod, self.maph, self.size, self.wall_texture
        )
        return pg.surfarray.make_surface(self.frame * 255)

    def is_on_track(self, posx, posy):
        """Verifica se o kart está na pista usando o canal alfa."""
        width, height = self.track_surface.shape[:2]
        # Converte a posição do mundo para coordenadas de pixel na imagem
        xx = int((posx / self.size) * (width - 1))
        yy = int((posy / self.size) * (height - 1))
        # Garante que os índices estejam dentro dos limites
        xx = np.clip(xx, 0, width - 1)
        yy = np.clip(yy, 0, height - 1)
        # Obtém o valor do canal alfa
        alpha = self.track_surface[yy, xx, 3]
        return alpha > 0.5

    def is_coin_on_track(self, posx, posy):
        """Verifica se o kart está na pista usando o canal alfa."""
        width, height = self.track_surface.shape[:2]
        # Converte a posição do mundo para coordenadas de pixel na imagem
        xx = int((posx / self.size) * (width - 1))
        yy = int((posy / self.size) * (height - 1))
        # Garante que os índices estejam dentro dos limites
        xx = np.clip(xx, 0, width - 1)
        yy = np.clip(yy, 0, height - 1)
        # Obtém o valor do canal alfa
        alpha = self.track_surface[yy, xx, 3]
        return alpha > 0.5

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, hres, halfvres, mod, maph, size, wall_texture):
    """Função otimizada que gera o frame atual usando raycasting."""
    for i in range(hres):
        # Calcula o ângulo atual
        rot_i = rot + np.deg2rad(i / mod - 30)
        sin_rot, cos_rot = np.sin(rot_i), np.cos(rot_i)
        cos2 = np.cos(np.deg2rad(i / mod - 30))
        sky_index = int(np.rad2deg(rot_i) % 359)
        frame[i][:] = sky[sky_index][:]

        for j in range(halfvres):
            # Calcula a distância até o próximo ponto
            n = (halfvres / (halfvres - j)) / cos2
            x = posx + cos_rot * n
            y = posy + sin_rot * n
            xx = int(x / 30 % 1 * 1023)
            yy = int(y / 30 % 1 * 1023)
            shade = 0.95 + 0.05 * (1 - j / halfvres)

            # Verifica se há uma parede
            map_x, map_y = int(x) % size, int(y) % size
            if maph[map_x][map_y] == 1:
                # Desenha a parede
                h = halfvres - j
                c = shade * wall_texture[int(x * 10 % 100)][int(y * 10 % 100)]
                min_k = max(0, halfvres - h)
                max_k = min(frame.shape[1], halfvres + h)
                frame[i][min_k:max_k] = c
                break
            else:
                # Desenha o chão
                frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade

    return frame

class SoundManager:
    def __init__(self):
        # Carrega e toca a música de fundo
        pg.mixer.music.load('assets/nirvana.mp3')
        pg.mixer.music.play(-1)
        pg.mixer.music.set_volume(0.3)
        
        # Sons de eventos
        self.item_sound = pg.mixer.Sound('assets/item.mp3')
        self.boost_sound = pg.mixer.Sound('assets/boost.mp3')
        self.unboost_sound = pg.mixer.Sound('assets/unboost.mp3')
        self.coin_up_sound = pg.mixer.Sound('assets/coin_up.mp3')
        self.coin_down_sound = pg.mixer.Sound('assets/coin_down.mp3')
        
        # Sons de vitória e derrota
        self.victory_sound = pg.mixer.Sound('assets/victory.mp3')
        self.lose_sound = pg.mixer.Sound('assets/lose.mp3')
        
        # Controle de volume dos sons
        self.item_sound.set_volume(0.5)
        self.boost_sound.set_volume(0.5)
        self.unboost_sound.set_volume(0.5)
        self.coin_up_sound.set_volume(0.5)
        self.coin_down_sound.set_volume(0.5)
        self.victory_sound.set_volume(0.5)
        self.lose_sound.set_volume(0.5)

class Game:
    def __init__(self):
        pg.init()
        # Configura a tela e o relógio
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        # Inicializa o kart, o renderizador e o gerenciador de som
        self.kart = Kart()
        self.renderer = Renderer(120, 100)
        self.sound_manager = SoundManager()
        # Carrega os sprites e os assets
        self.load_sprites()
        self.initialize_game_variables()
        self.initialize_joysticks()
        self.load_assets()
        
        # Inicializa a porta serial
        try:
            self.serial_port = serial.Serial('COM5', 115200, timeout=0)
            print("Porta serial COM5 aberta com sucesso.")
        except serial.SerialException:
            print("Erro: Não foi possível abrir a porta serial COM5")
            self.serial_port = None
            
        # Variáveis para os dados do sensor
        self.sensor_ay = 0
        self.sensor_button1 = 0
        self.sensor_button2 = 0

    def initialize_game_variables(self):
        """Inicializa as variáveis do jogo."""
        self.running = True
        self.controls_enabled = False
        self.lap_count = 0
        self.has_crossed_finish_line = False
        self.current_power = None
        self.power_activation_time = None
        self.power_in_use = False
        self.powers = ['Boost', 'Un-Boost', 'Moeda :)', 'Moeda :(', 'Volta :)', 'Volta :(']
        self.coin_count = 0
        self.start_time = None
        self.game_over = False
        self.game_over_time = None
        self.game_result = None
        self.restart_game = False

    def initialize_joysticks(self):
        """Inicializa os joysticks conectados."""
        pg.joystick.init()
        self.joysticks = []
        for i in range(pg.joystick.get_count()):
            joystick = pg.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)

    def load_sprites(self):
        """Carrega e prepara os sprites do jogo."""
        mario_sheet = pg.image.load('assets/mario_sheet.png').convert_alpha()
        sprite_width, sprite_height, sprite_scale = 32, 32, 6.5
        positions = [(5.55, 1.1), (4.6, 1.1), (7.38, 1.1)]
        sprites = []
        for x, y in positions:
            sprite = mario_sheet.subsurface(pg.Rect(x * sprite_width, y * sprite_height, sprite_width, sprite_height))
            sprite = pg.transform.scale(sprite, (int(sprite_width * sprite_scale), int(sprite_height * sprite_scale)))
            sprites.append(sprite)
        self.mario_w, self.mario_a, self.mario_d = sprites
        self.kart_sprite = pg.transform.scale(pg.image.load('assets/kart.png'), (200, 200))
        self.current_sprite = self.mario_w

    def load_assets(self):
        """Carrega fontes, imagens e sons necessários."""
        pg.font.init()
        self.font = pg.font.SysFont('Arial', 24)
        self.font_2 = pg.font.SysFont('Arial', 48)
        self.countdown_images = [pg.image.load(f'assets/{i}.png') for i in ['3', '2', '1', 'go']]
        self.countdown_sound = 'assets/ct.mp3'
        self.box_sprite = pg.transform.scale(pg.image.load('assets/box.png').convert_alpha(), (50, 50))
        self.coin_sound = pg.mixer.Sound('assets/moeda.mp3')
        self.coin_sound.set_volume(0.1)
        self.coin_sprite = pg.image.load('assets/moeda.png').convert_alpha()
        self.initialize_game_objects()

    def initialize_game_objects(self):
        """Inicializa as caixas de itens e as moedas."""
        # Caixas de itens com posição, estado e tempo de respawn
        self.item_boxes = [
            {'posx': 26.70, 'posy': 14.90, 'active': True, 'respawn_time': None},
            {'posx': 27.41, 'posy': 14.90, 'active': True, 'respawn_time': None},
            {'posx': 28.12, 'posy': 14.90, 'active': True, 'respawn_time': None},
            {'posx': 11.00, 'posy': 4.80, 'active': True, 'respawn_time': None},
            {'posx': 11.27, 'posy': 4.06, 'active': True, 'respawn_time': None},
            {'posx': 11.70, 'posy': 3.32, 'active': True, 'respawn_time': None}
        ]
        # Gerar 15 moedas em posições aleatórias dentro da pista
        self.coins = []
        num_coins = 15
        while len(self.coins) < num_coins:
            # Gerar posx e posy aleatórios dentro dos limites do mapa
            posx = random.uniform(0, self.renderer.size)
            posy = random.uniform(0, self.renderer.size)
            # Verificar se a posição está na pista
            if self.renderer.is_coin_on_track(posx, posy):
                self.coins.append({'posx': posx, 'posy': posy})
                
    def read_sensor_data(self):
        """Lê os dados da porta serial e atualiza as entradas do sensor."""
        if self.serial_port:
            try:
                line = self.serial_port.readline().decode('utf-8').rstrip()
                if line:
                    #print(f"Linha recebida: '{line}'")  # Adicione esta linha
                    # Analisa a linha
                    data_parts = line.split(',')
                    for part in data_parts:
                        if part.startswith('ay:'):
                            value_str = part[3:]
                            if value_str.strip() != '':
                                self.sensor_ay = int(value_str)
                        elif part.startswith('button1:'):
                            value_str = part[8:]
                            if value_str.strip() != '':
                                self.sensor_button1 = int(value_str)

                        elif part.startswith('button2:'):
                            value_str = part[8:]
                            if value_str.strip() != '':
                                self.sensor_button2 = int(value_str)

            except (UnicodeDecodeError, ValueError) as e:
                print(f"Erro ao analisar os dados seriais: {e}")

    def handle_input(self):
        """Processa a entrada de teclas e joystick."""
        keys = pg.key.get_pressed()
        turn_value = (keys[pg.K_RIGHT] or keys[pg.K_d]) - (keys[pg.K_LEFT] or keys[pg.K_a])
        accelerate_value = keys[pg.K_UP] or keys[pg.K_w]
        brake_value = keys[pg.K_DOWN] or keys[pg.K_s]

        # Entrada do joystick
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
                
        # Entrada do sensor
        self.read_sensor_data()
        if self.sensor_ay != 0:
            # Normaliza o valor de 'ay' para um intervalo entre -1 e 1
            max_ay = 16384  # Sensibilidade ajustada para o MPU6050
            normalized_ay = self.sensor_ay / max_ay
            # Supondo que 'ay' positivo significa virar à direita
            turn_value -= normalized_ay * 0.5  # Multiplicar para ajustar a sensibilidade

        if self.sensor_button1 == 1:
            accelerate_value += 1
        if self.sensor_button2 == 1:
            brake_value += 1
            
        # Limita 'turn_value' entre -1 e 1
        turn_value = max(-1, min(1, turn_value))

        # Atualiza o movimento do kart
        self.kart.handle_movement(turn_value, accelerate_value, brake_value)
        # Atualiza o sprite atual
        self.update_current_sprite(turn_value, brake_value)

    def update_current_sprite(self, turn_value, brake_value):
        """Atualiza o sprite do kart com base no movimento."""
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
        for image in self.countdown_images:
            self.render_game_frame()
            self.screen.blit(image, image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
            pg.display.update()
            pg.time.wait(1000)
        while pg.mixer.music.get_busy():
            pg.time.wait(100)
        self.sound_manager = SoundManager()
        self.controls_enabled = True

    def check_finish_line(self):
        """Verifica se o kart cruzou a linha de chegada."""
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
        """Renderiza o quadro atual do jogo."""
        camera_offset = -1.0  # Desloca a câmera para trás do kart
        camera_x = self.kart.posx + np.cos(self.kart.rot) * camera_offset
        camera_y = self.kart.posy + np.sin(self.kart.rot) * camera_offset
        frame_surface = self.renderer.render_frame(camera_x, camera_y, self.kart.rot)
        self.draw_objects(frame_surface, camera_x, camera_y)  # Passa a posição da câmera
        frame_surface = pg.transform.scale(frame_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(frame_surface, (0, 0))
        self.screen.blit(self.current_sprite, self.current_sprite.get_rect(center=(400, 600 - 120)))
        self.draw_ui()

    def draw_objects(self, frame_surface, camera_x, camera_y):
        """Desenha as caixas de itens e moedas na tela."""
        self.draw_sprites(frame_surface, self.item_boxes, self.box_sprite, camera_x, camera_y, is_active_key='active')
        self.draw_sprites(frame_surface, self.coins, self.coin_sprite, camera_x, camera_y)

    def draw_sprites(self, frame_surface, objects, sprite_image, camera_x, camera_y, is_active_key=None):
        """Desenha sprites na tela com base na posição relativa à câmera."""
        for obj in objects:
            if is_active_key and not obj.get(is_active_key, True):
                continue
            dx = obj['posx'] - camera_x
            dy = obj['posy'] - camera_y
            distance = np.hypot(dx, dy)
            angle_to_obj = np.arctan2(dy, dx)
            angle_difference = (angle_to_obj - self.kart.rot + np.pi) % (2 * np.pi) - np.pi

            if abs(angle_difference) < np.deg2rad(30):
                # Calcula a posição na tela
                hres = self.renderer.hres
                halfvres = self.renderer.halfvres
                screen_x = (angle_difference / np.deg2rad(30)) * (hres / 2) + (hres / 2)
                corrected_distance = max(0.1, distance)
                K = 70  # Constante para ajustar o tamanho do sprite
                sprite_height = int(K / corrected_distance)
                sprite_height = np.clip(sprite_height, 5, 200)
                aspect_ratio = (0.5 * sprite_image.get_width()) / sprite_image.get_height()
                sprite_width = int(sprite_height * aspect_ratio)
                sprite = pg.transform.scale(sprite_image, (sprite_width, sprite_height))
                screen_ground_y = halfvres + (halfvres / corrected_distance)
                near_distance = 2
                max_offset = 50
                vertical_offset = max_offset * (1 - (corrected_distance / near_distance)) if corrected_distance < near_distance else 0
                screen_y = screen_ground_y - sprite_height - vertical_offset
                if 0 <= screen_x - sprite_width / 2 <= hres and 0 <= screen_y <= halfvres * 2:
                    frame_surface.blit(sprite, (screen_x - sprite_width / 2, screen_y))

    def draw_ui(self):
        """Desenha a interface do usuário (HUD)."""
        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)
        self.draw_text(f'Moedas: {self.coin_count}', SCREEN_WIDTH - 10, 10, align_right=True)
        power_text = 'Poder: Nenhum' if self.current_power is None else f'Poder: {self.current_power}'
        self.draw_text(power_text, 10, 70)

        # Adicionar o tempo decorrido
        if self.start_time is not None:
            elapsed_time_ms = pg.time.get_ticks() - self.start_time
            elapsed_seconds = int(elapsed_time_ms / 1000)
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            time_str = f'Tempo: {minutes:02}:{seconds:02}'
            self.draw_text(time_str, SCREEN_WIDTH - 10, 40, align_right=True)

    def draw_text(self, text, x, y, align_right=False):
        """Desenha texto na tela."""
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(topright=(x, y)) if align_right else text_surface.get_rect(topleft=(x, y))
        self.screen.blit(text_surface, text_rect)

    def check_collisions(self):
        """Verifica colisões com moedas e caixas de itens."""
        self.check_coin_collisions()
        self.check_item_box_collisions()

    def check_coin_collisions(self):
        """Verifica se o kart coletou alguma moeda."""
        coins_to_remove = []
        for coin in self.coins:
            if self.is_colliding(self.kart, coin):
                self.coin_sound.play()
                self.coin_count += 1
                coins_to_remove.append(coin)
        for coin in coins_to_remove:
            self.coins.remove(coin)

    def check_item_box_collisions(self):
        """Verifica se o kart colidiu com alguma caixa de item."""
        if self.current_power is None and not self.power_in_use:
            for box in self.item_boxes:
                if box['active'] and self.is_colliding(self.kart, box):
                    box['active'] = False
                    box['respawn_time'] = pg.time.get_ticks() + 10000  # 10 segundos para reaparecer
                    self.sound_manager.item_sound.play()  # Toca som ao coletar item
                    self.current_power = "Press X / R"
                    break

    @staticmethod
    def is_colliding(obj1, obj2, threshold=0.1):
        """Verifica se dois objetos estão colidindo."""
        dx = obj2['posx'] - obj1.posx
        dy = obj2['posy'] - obj1.posy
        distance = np.hypot(dx, dy)
        return distance < threshold

    def activate_power(self):
        """Ativa um poder aleatório."""
        self.current_power = random.choice(self.powers)
        self.power_activation_time = pg.time.get_ticks()
        self.power_in_use = True

        # Aplica o efeito do poder e toca o som apropriado
        if self.current_power == 'Boost':
            self.kart.max_speed *= 1.5
            self.sound_manager.boost_sound.play()
        elif self.current_power == 'Un-Boost':
            self.kart.max_speed *= 0.5
            self.sound_manager.unboost_sound.play()
        elif self.current_power == 'Moeda :)':
            self.coin_count += 1
            self.sound_manager.coin_up_sound.play()
        elif self.current_power == 'Moeda :(':
            self.coin_count = max(0, self.coin_count - 1)
            self.sound_manager.coin_down_sound.play()
        elif self.current_power == 'Volta :)':
            self.lap_count = max(0, self.lap_count - 1)
            self.sound_manager.coin_up_sound.play()
        elif self.current_power == 'Volta :(':
            self.lap_count += 1
            self.sound_manager.coin_down_sound.play()

    def update_powers(self):
        """Atualiza o estado dos poderes ativos."""
        if self.power_in_use and pg.time.get_ticks() - self.power_activation_time >= 5000:
            # Desativa o efeito do poder após 5 segundos
            if self.current_power == 'Boost':
                self.kart.max_speed /= 1.5
            elif self.current_power == 'Un-Boost':
                self.kart.max_speed /= 0.5
            self.current_power = None
            self.power_in_use = False

    def respawn_boxes(self):
        """Reativa caixas de itens após o tempo de respawn."""
        current_time = pg.time.get_ticks()
        for box in self.item_boxes:
            if not box['active'] and box['respawn_time'] and current_time >= box['respawn_time']:
                box['active'] = True
                box['respawn_time'] = None

    def show_loading_screen(self):
        """Exibe a tela de carregamento."""
        self.screen.fill((0, 0, 0))
        text_surface = self.font_2.render("Carregando...", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)
        pg.display.update()
        
    def show_victory_screen(self):
        """Exibe a tela de vitória."""
        # Carregar a imagem de fundo
        background = pg.image.load('assets/fundo.png')
        self.screen.blit(background, (0, 0))
        # Calcular tempo total
        total_time = (self.game_over_time - self.start_time) / 1000  # em segundos
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        time_str = f"{minutes} minutos e {seconds} segundos" if minutes > 0 else f"{seconds} segundos"
        message = f"Parabéns, você coletou as 10 moedas em {time_str} e em {self.lap_count} voltas!"
        # Renderizar a mensagem
        text_surface = self.font_2.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text_surface, text_rect)
        # Exibir os botões
        self.show_end_screen_buttons()
        pg.display.update()

    def show_lose_screen(self):
        """Exibe a tela de derrota."""
        # Carregar a imagem de fundo
        background = pg.image.load('assets/fundo.png')
        self.screen.blit(background, (0, 0))
        # Mensagem
        message = f"Você perdeu! Coletou {self.coin_count} moedas."
        # Renderizar a mensagem
        text_surface = self.font_2.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text_surface, text_rect)
        # Exibir os botões
        self.show_end_screen_buttons()
        pg.display.update()
        
    def show_end_screen_buttons(self):
        """Exibe os botões de 'play' e 'exit' na tela final."""
        # Carregar os botões
        play_button = pg.transform.scale(pg.image.load('assets/play.png'), (200, 80))
        exit_button = pg.transform.scale(pg.image.load('assets/exit.png'), (200, 80))
        # Definir as posições dos botões (lado a lado)
        play_button_rect = play_button.get_rect(center=(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
        exit_button_rect = exit_button.get_rect(center=(SCREEN_WIDTH // 2 + 110, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(play_button, play_button_rect)
        self.screen.blit(exit_button, exit_button_rect)
        # Salvar os retângulos dos botões para detecção de clique
        self.end_screen_play_button_rect = play_button_rect
        self.end_screen_exit_button_rect = exit_button_rect
            
    def wait_for_menu_selection(self):
        """Espera a seleção do jogador na tela final."""
        waiting = True
        while waiting:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    mouse_pos = pg.mouse.get_pos()
                    if self.end_screen_play_button_rect.collidepoint(mouse_pos):
                        # **Reiniciar o jogo**
                        waiting = False
                        self.running = False  # Sair do jogo atual
                        # Definir uma flag para reiniciar no menu
                        self.restart_game = True
                    elif self.end_screen_exit_button_rect.collidepoint(mouse_pos):
                        # **Sair do jogo**
                        waiting = False
                        self.running = False
            pg.time.wait(100)

    def run(self):
        """Método principal que executa o loop do jogo."""
        self.show_loading_screen()
        pg.time.wait(2000)
        self.countdown()
        
        self.start_time = pg.time.get_ticks()

        while self.running:
            power_button_pressed = False
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.running = False
                elif event.type == pg.KEYDOWN and event.key == pg.K_r:
                    power_button_pressed = True
                elif event.type == pg.JOYBUTTONDOWN:
                    if event.button == 2:
                        power_button_pressed = True

            if self.controls_enabled:
                self.handle_input()
                if power_button_pressed and self.current_power == "Press X / R" and not self.power_in_use:
                    self.activate_power()

                et = self.clock.tick()
                on_track = self.renderer.is_on_track(self.kart.posx, self.kart.posy)
                self.kart.update(et, on_track, self.renderer.maph, self.renderer.size)
                self.check_finish_line()
                self.check_collisions()
                self.update_powers()
                self.respawn_boxes()

            self.render_game_frame()
            pg.display.update()
            
            if not self.game_over:
                # **Verificar condições de vitória e derrota**
                current_time = pg.time.get_ticks()
                elapsed_time = (current_time - self.start_time) / 1000  # Tempo em segundos
                if self.coin_count >= 10 and elapsed_time <= 9999 and self.lap_count <= 10:
                    # **Jogador venceu**
                    self.game_over = True
                    self.game_over_time = current_time
                    self.game_result = 'win'
                    # Parar a música de fundo
                    pg.mixer.music.stop()
                    # Tocar som de vitória
                    self.sound_manager.victory_sound.play()
                elif elapsed_time > 9999 or self.lap_count >= 10:
                    # **Jogador perdeu**
                    self.game_over = True
                    self.game_over_time = current_time
                    self.game_result = 'lose'
                    # Parar a música de fundo
                    pg.mixer.music.stop()
                    # Tocar som de derrota
                    self.sound_manager.lose_sound.play()
                    
            # **Mover o bloco abaixo para fora do 'if not self.game_over:'**
            if self.game_over:
                # **Esperar 3 segundos antes de mostrar a tela final**
                if pg.time.get_ticks() - self.game_over_time >= 3000:
                    if self.game_result == 'win':
                        self.show_victory_screen()
                    else:
                        self.show_lose_screen()
                    # Pausar para permitir que o jogador veja a tela final
                    self.wait_for_menu_selection()
                    # Depois que o jogador faz uma seleção, sair do loop
                    self.running = False
                    break  # Sair do loop do jogo
                    
        # Fecha a porta serial quando o jogo termina
        if self.serial_port:
            self.serial_port.close()

def menu():
    """Exibe o menu principal do jogo."""
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("Menu")

    # Carrega as imagens do menu
    background = pg.image.load('assets/fundo.png')
    play_button = pg.transform.scale(pg.image.load('assets/play.png'), (200, 80))
    exit_button = pg.transform.scale(pg.image.load('assets/exit.png'), (200, 80))

    # Define as posições dos botões
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
                    game = Game()
                    game.run()
                    # **Verificar se o jogador selecionou reiniciar o jogo**
                    if game.restart_game:
                        continue  # Reiniciar o loop para começar o jogo novamente
                    else:
                        running = False  # Sair se o jogador não quiser reiniciar
                elif exit_button_rect.collidepoint(mouse_pos):
                    running = False

        pg.display.update()

if __name__ == '__main__':
    menu()
    pg.quit()