import numpy as np
import pygame as pg
from numba import njit  # Importa o decorador njit para otimização de funções numéricas

class Renderer:
    def __init__(self, hres, halfvres):
        self.hres, self.halfvres = hres, halfvres
        self.mod = hres / 60
        self.size = 32
        self.maph = np.zeros((self.size, self.size), dtype=int)
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))
        self.load_assets()
        
        self.maph[0, :] = 1
        self.maph[:, 0] = 1
        self.maph[self.size - 1, :] = 1
        self.maph[:, self.size - 1] = 1

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
        
        # Carregar a textura azul para as paredes
        blue_texture = np.zeros((100, 100, 3))
        blue_texture[:, :] = [0, 0, 1]  # Cor azul em RGB normalizado (0 a 1)
        self.wall_texture = blue_texture

        # Obtém as dimensões da textura do chão
        self.floor_width, self.floor_height = self.floor.shape[0], self.floor.shape[1]

    def render_frame(self, posx, posy, rot):
        # Chama a função otimizada para gerar um novo frame com base na posição e rotação do kart
        self.frame = new_frame(
            posx, posy, rot, self.frame, self.sky, self.floor,
            self.track_surface, self.border_surface,
            self.hres, self.halfvres, self.mod, self.maph, self.size, self.wall_texture
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
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, border_surface, hres, halfvres, mod, maph, size, wall_texture):
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

'''
#Versão pré renderer
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
        
        self.size = 4
        self.maph = np.random.choice([0, 0, 0, 1], (self.size, self.size))
        
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
            self.track_surface, self.border_surface, self.hres, self.halfvres, self.mod, self.maph, self.size
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
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, border_surface, hres, halfvres, mod, maph, size):
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
            
            if maph[int(x) % (size - 1)][int(y) % (size - 1)]:
                h = halfvres - j
                c = shade * np.ones(3)
                for k in range(h * 2):
                    frame[i][halfvres - h + k] = c
                break
            else:
                frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade
    return frame
'''
