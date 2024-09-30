import pygame as pg
from kart import Kart
from renderer import Renderer
from sound_manager import SoundManager
import numpy as np

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

    def load_sprites(self):
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

    '''Captura o estado atual das teclas pressionadas e mapeia essas teclas para valores de direção'''
    def handle_input(self):
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

                # Zona morta
                deadzone = 0.1

                # Atualiza o valor de virada com base no eixo horizontal
                if abs(axis_horizontal) > deadzone:
                    turn_value = axis_horizontal  # Valor entre -1.0 e 1.0

                # Normaliza o valor do gatilho esquerdo
                left_trigger_value = (trigger_axis_left + 1) / 2  # Varia de 0 (não pressionado) a 1 (pressionado)

                # Mapeia o eixo dos gatilhos compartilhados para acelerar e frear
                if left_trigger_value > deadzone:
                    brake_value = left_trigger_value
                else:
                    brake_value = 0.0
                    
                trigger_axis_right = joystick.get_axis(5)
                right_trigger_value = (trigger_axis_right + 1) / 2  # Normaliza para 0 a 1

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
        finish_line_x_min = 26.25
        finish_line_x_max = 28.7
        finish_line_y = 17.5

        # Verifica se o kart está dentro das coordenadas da linha de chegada
        if finish_line_x_min <= self.kart.posx <= finish_line_x_max and abs(self.kart.posy - finish_line_y) < 0.1:
            # Verifica se o kart está se movendo para frente
            if self.kart.vel > 0:
                # Se ainda não cruzou a linha nesta volta, incrementa o contador de voltas
                if not self.has_crossed_finish_line:
                    self.lap_count += 1
                    self.has_crossed_finish_line = True
            else:
                # Se o kart estiver parado ou se movendo para trás, reseta a flag
                self.has_crossed_finish_line = False
        else:
            # Se o kart não está na linha de chegada, reseta a flag
            self.has_crossed_finish_line = False

    '''Usa o Renderer para renderizar a pista com base na posição e rotação do kart'''
    def render_game_frame(self):
        et = self.clock.tick()
        frame_surface = self.renderer.render_frame(self.kart.posx, self.kart.posy, self.kart.rot)
        frame_surface = pg.transform.scale(frame_surface, (800, 600))
        self.screen.blit(frame_surface, (0, 0))
        
        sprite_rect = self.current_sprite.get_rect(center=(400, 600 - 120))
        self.screen.blit(self.current_sprite, sprite_rect)
        
        sprite_rect = self.current_sprite.get_rect(center=(400, 600 - 120))
        self.screen.blit(self.current_sprite, sprite_rect)
        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)


    def draw_text(self, text, x, y):
        text_surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (x, y))
        
    '''Tela de carregamento enquanto os recursos do jogo são preparados'''
    def show_loading_screen(self):
        
        self.screen.fill((0, 0, 0))
        font = pg.font.SysFont('Arial', 48)
        text_surface = font.render("Carregando...", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(400, 300))
        self.screen.blit(text_surface, text_rect)
        pg.display.update()

    def run(self):
        # Exibe a tela de carregamento antes de começar o jogo
        self.show_loading_screen()

        pg.time.wait(2000)  # Aguarda 2 segundos

        #inicia o countdown
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
      
'''      
#Versão pré renderer
import pygame as pg
from kart import Kart
from renderer import Renderer
from sound_manager import SoundManager

class Game:
    def __init__(self):
        # Inicializa todos os módulos do Pygame
        pg.init()
        # Define o tamanho da janela do jogo
        self.screen = pg.display.set_mode((800, 600))
        # Cria um objeto Clock para controlar o FPS
        self.clock = pg.time.Clock()
        # Cria uma instância do kart do jogador
        self.kart = Kart()
        # Cria uma instância do renderizador para gerar os gráficos do jogo
        self.renderer = Renderer(120, 100)
        # Gerencia os sons do jogo (música de fundo, efeitos sonoros, etc.)
        self.sound_manager = SoundManager()
        # Carrega os sprites necessários para o jogo
        self.load_sprites()
        # Variável que controla se o jogo está rodando
        self.running = True
        # Inicialmente, os controles estão desativados até o fim do countdown
        self.controls_enabled = False
        # Contador de voltas do jogador
        self.lap_count = 0
        # Flag para verificar se o jogador já cruzou a linha de chegada
        self.has_crossed_finish_line = False

        # Inicializa o módulo de fontes do Pygame
        pg.font.init()
        # Define a fonte padrão para exibir textos na tela
        self.font = pg.font.SysFont('Arial', 24)

        # Carrega as imagens e o som usados no countdown
        self.countdown_images = [
            pg.image.load('assets/3.png'),
            pg.image.load('assets/2.png'),
            pg.image.load('assets/1.png'),
            pg.image.load('assets/go.png')
        ]
        self.countdown_sound = 'assets/ct.mp3'

    def load_sprites(self):
        # Carrega a folha de sprites do Mario com transparência
        mario_sheet = pg.image.load('assets/mario_sheet.png').convert_alpha()
        # Define as dimensões e a escala dos sprites
        sprite_width, sprite_height, sprite_scale = 32, 32, 6.5
        # Extrai e redimensiona o sprite do Mario olhando para frente
        self.mario_w = pg.transform.scale(
            mario_sheet.subsurface(pg.Rect(5.55 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
            (sprite_width * sprite_scale, sprite_height * sprite_scale)
        )
        # Extrai e redimensiona o sprite do Mario virando à esquerda
        self.mario_a = pg.transform.scale(
            mario_sheet.subsurface(pg.Rect(4.6 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
            (sprite_width * sprite_scale, sprite_height * sprite_scale)
        )
        # Extrai e redimensiona o sprite do Mario virando à direita
        self.mario_d = pg.transform.scale(
            mario_sheet.subsurface(pg.Rect(7.38 * sprite_width, 1.1 * sprite_height, sprite_width, sprite_height)),
            (sprite_width * sprite_scale, sprite_height * sprite_scale)
        )
        # Carrega e redimensiona o sprite do kart
        self.kart_sprite = pg.transform.scale(pg.image.load('assets/kart.png'), (200, 200))
        # Define o sprite atual como o Mario olhando para frente
        self.current_sprite = self.mario_w

    def handle_input(self):
        # Captura o estado de todas as teclas
        keys = pg.key.get_pressed()
        # Atualiza o sprite atual com base na tecla pressionada
        if keys[pg.K_LEFT] or keys[ord('a')]:
            # Se a tecla esquerda ou 'A' for pressionada, mostra o sprite virando à esquerda
            self.current_sprite = self.mario_a
        elif keys[pg.K_RIGHT] or keys[ord('d')]:
            # Se a tecla direita ou 'D' for pressionada, mostra o sprite virando à direita
            self.current_sprite = self.mario_d
        elif keys[pg.K_DOWN] or keys[ord('s')]:
            # Se a tecla para baixo ou 'S' for pressionada, mostra o sprite do kart
            self.current_sprite = self.kart_sprite
        else:
            # Caso contrário, mostra o sprite olhando para frente
            self.current_sprite = self.mario_w

    def countdown(self):
        # Carrega e toca o som do countdown
        pg.mixer.music.load(self.countdown_sound)
        pg.mixer.music.play()
        # Loop para exibir as imagens do countdown (3, 2, 1, GO)
        for i in range(4):
            # Renderiza o quadro do jogo (fundo, pista, etc.)
            self.render_game_frame()
            # Calcula a posição centralizada para a imagem do countdown
            self.screen.blit(
                self.countdown_images[i],
                (400 - self.countdown_images[i].get_width() // 2, 300 - self.countdown_images[i].get_height() // 2)
            )
            # Atualiza a tela para exibir as mudanças
            pg.display.update()
            # Espera 1 segundo antes de mostrar a próxima imagem
            pg.time.wait(1000)
        # Aguarda até que o som do countdown termine de tocar
        while pg.mixer.music.get_busy():
            pg.time.wait(100)
        # Inicia o gerenciador de som (música de fundo do jogo)
        self.sound_manager = SoundManager()
        # Ativa os controles do jogador após o countdown
        self.controls_enabled = True

    def check_finish_line(self):
        # Define as coordenadas da linha de chegada
        finish_line_x_min = 26.25
        finish_line_x_max = 28.7
        finish_line_y = 17.5

        # Verifica se o kart está dentro das coordenadas da linha de chegada
        if finish_line_x_min <= self.kart.posx <= finish_line_x_max and abs(self.kart.posy - finish_line_y) < 0.1:
            # Verifica se o kart está se movendo para frente
            if self.kart.vel > 0:
                # Se ainda não cruzou a linha nesta volta, incrementa o contador de voltas
                if not self.has_crossed_finish_line:
                    self.lap_count += 1
                    self.has_crossed_finish_line = True
            else:
                # Se o kart estiver parado ou se movendo para trás, reseta a flag
                self.has_crossed_finish_line = False
        else:
            # Se o kart não está na linha de chegada, reseta a flag
            self.has_crossed_finish_line = False

    def render_game_frame(self):
        # Calcula o tempo desde o último quadro (delta time)
        et = self.clock.tick()
        # Renderiza o quadro atual do jogo usando o renderizador
        frame_surface = self.renderer.render_frame(self.kart.posx, self.kart.posy, self.kart.rot)
        # Redimensiona a superfície renderizada para caber na tela
        frame_surface = pg.transform.scale(frame_surface, (800, 600))
        # Desenha o quadro renderizado na tela
        self.screen.blit(frame_surface, (0, 0))
        # Obtém o retângulo do sprite atual para posicioná-lo corretamente
        sprite_rect = self.current_sprite.get_rect(center=(400, 600 - 120))
        # Desenha o sprite atual (kart) na tela
        self.screen.blit(self.current_sprite, sprite_rect)
        # Exibe informações na tela, como posição e voltas
        self.draw_text(f'Pos: ({self.kart.posx:.2f}, {self.kart.posy:.2f})', 10, 10)
        self.draw_text(f'Voltas: {self.lap_count}', 10, 40)

    def draw_text(self, text, x, y):
        # Renderiza o texto usando a fonte definida
        text_surface = self.font.render(text, True, (255, 255, 255))
        # Desenha o texto na posição especificada
        self.screen.blit(text_surface, (x, y))

    def show_loading_screen(self):
        """Exibe uma tela de carregamento enquanto os recursos do jogo são preparados."""
        # Preenche a tela com a cor preta
        self.screen.fill((0, 0, 0))
        # Define uma fonte maior para o texto de carregamento
        font = pg.font.SysFont('Arial', 48)
        # Renderiza o texto "Carregando..." em branco
        text_surface = font.render("Carregando...", True, (255, 255, 255))
        # Centraliza o texto na tela
        text_rect = text_surface.get_rect(center=(400, 300))
        # Desenha o texto na tela
        self.screen.blit(text_surface, text_rect)
        # Atualiza a tela para exibir o texto
        pg.display.update()

    def run(self):
        # Exibe a tela de carregamento antes de começar o jogo
        self.show_loading_screen()

        # Simula o carregamento de recursos (opcional)
        pg.time.wait(2000)  # Aguarda 2 segundos para simular o carregamento

        # Após carregar tudo, inicia o countdown
        self.countdown()

        # Loop principal do jogo
        while self.running:
            # Processa os eventos do Pygame
            for event in pg.event.get():
                # Se o jogador clicar no botão de fechar ou pressionar ESC, encerra o jogo
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.running = False
            # Se os controles estiverem habilitados (após o countdown)
            if self.controls_enabled:
                # Lida com a entrada do usuário (teclas pressionadas)
                self.handle_input()
                # Calcula o tempo desde o último quadro
                et = self.clock.tick()
                # Captura o estado das teclas pressionadas
                keys = pg.key.get_pressed()
                # Verifica se o kart está na pista ou na borda
                on_track = self.renderer.is_on_track(self.kart.posx, self.kart.posy)
                on_border = self.renderer.is_on_border(self.kart.posx, self.kart.posy)
                # Atualiza a posição e o estado do kart
                self.kart.update(keys, et, on_track, on_border)
                # Verifica se o jogador cruzou a linha de chegada
                self.check_finish_line()
            # Renderiza o quadro atual do jogo
            self.render_game_frame()
            # Atualiza a tela com o novo quadro
            pg.display.update()
'''