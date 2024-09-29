import numpy as np
import pygame as pg
from numba import njit  # Importa o decorador njit para otimização de funções numéricas

class Renderer:
    def __init__(self, hres, halfvres):
        # Define a resolução horizontal (hres) e metade da resolução vertical (halfvres)
        self.hres, self.halfvres = hres, halfvres
        # Calcula um modificador para ajustes de ângulo
        self.mod = hres / 60
        # Cria um frame inicial com valores aleatórios (ruído)
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))
        # Carrega os recursos gráficos necessários
        self.load_assets()

    def load_assets(self):
        # Carrega e escala a imagem do céu, convertendo-a em um array 3D normalizado (valores entre 0 e 1)
        self.sky = pg.surfarray.array3d(
            pg.transform.scale(
                pg.image.load('assets/skybox.jpg'),
                (360, self.halfvres * 2)
            )
        ) / 255

        # Carrega a textura do chão (pista), convertendo-a em um array 3D normalizado
        self.floor = pg.surfarray.array3d(
            pg.image.load('assets/MarioKart.png')
        ) / 255

        # Carrega a máscara que define onde é pista (track) e onde não é
        self.track_surface = pg.surfarray.array3d(
            pg.image.load('assets/pista.png').convert_alpha()
        ) / 255

        # Carrega a máscara que define as bordas da pista
        self.border_surface = pg.surfarray.array3d(
            pg.image.load('assets/borda.png').convert_alpha()
        ) / 255

        # Obtém as dimensões da textura do chão
        self.floor_width, self.floor_height = self.floor.shape[0], self.floor.shape[1]

    def render_frame(self, posx, posy, rot):
        # Chama a função otimizada para gerar um novo frame com base na posição e rotação do kart
        self.frame = new_frame(
            posx, posy, rot, self.frame, self.sky, self.floor,
            self.track_surface, self.border_surface, self.hres, self.halfvres, self.mod
        )
        # Converte o array do frame em uma superfície do Pygame para exibição
        return pg.surfarray.make_surface(self.frame * 255)

    def is_on_track(self, posx, posy):
        # Calcula as coordenadas na textura da pista com base na posição do kart
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        # Retorna True se a média dos valores de cor no ponto for maior que 0.5 (indicando pista)
        return np.mean(self.track_surface[xx][yy]) > 0.5

    def is_on_border(self, posx, posy):
        # Calcula as coordenadas na textura da borda com base na posição do kart
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        # Verifica se as coordenadas estão próximas das bordas da textura (margem de 5 pixels)
        if (yy < 5 or yy > 973) or (xx < 5 or xx > 973):
            return True
        return False

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, border_surface, hres, halfvres, mod):
    # Loop para cada coluna horizontal na resolução definida
    for i in range(hres):
        # Calcula o ângulo de visão atual, ajustando com base no campo de visão
        rot_i = rot + np.deg2rad(i / mod - 30)
        # Calcula os valores de seno e cosseno do ângulo atual
        sin, cos = np.sin(rot_i), np.cos(rot_i)
        # Compensa a distorção da projeção em 3D
        cos2 = np.cos(np.deg2rad(i / mod - 30))
        # Define a linha do céu correspondente ao ângulo atual
        frame[i][:] = sky[int(np.rad2deg(rot_i) % 359)][:]

        # Loop para cada linha vertical na metade inferior da tela (chão)
        for j in range(halfvres):
            # Calcula a distância projetada para o ponto atual
            n = (halfvres / (halfvres - j)) / cos2
            # Calcula as coordenadas reais no mundo para o ponto atual
            x = posx + cos * n
            y = posy + sin * n
            # Converte as coordenadas reais para índices na textura do chão
            xx = int(x / 30 % 1 * 1023)
            yy = int(y / 30 % 1 * 1023)
            # Aplica um sombreamento gradual com base na distância
            shade = 0.95 + 0.05 * (1 - j / halfvres)
            # Define a cor do pixel atual no frame aplicando a textura do chão e o sombreamento
            frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade
    return frame
