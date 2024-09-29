import numpy as np
import pygame as pg

class Kart:
    def __init__(self):
        # Inicializa a posição (posx, posy), rotação (rot) e velocidade (vel) do kart
        self.posx, self.posy, self.rot, self.vel = 27, 18.5, 4.7, 0  # Posição inicial ajustada
        # Parâmetros de movimento
        self.acceleration = 0.00001           # Taxa de aceleração ao acelerar
        self.deceleration = 0.00001           # Taxa de desaceleração natural
        self.brake_deceleration = 0.0003      # Taxa de desaceleração ao frear
        self.max_speed = 0.01                 # Velocidade máxima para frente
        self.min_speed = -0.005               # Velocidade máxima para trás (marcha à ré)
        self.slow_down_factor = 0.8           # Fator de redução de velocidade fora da pista

    def update(self, keys, et, on_track, on_border):
        # Se o kart ESTIVER na pista, não aplica redução de velocidade
        if on_track:
            self.vel *= self.slow_down_factor  # Mantém a velocidade normal na pista

        # Atualiza a rotação com base nas teclas de direção
        # Se a tecla da direita ou 'D' for pressionada, aumenta a rotação (vira à direita)
        # Se a tecla da esquerda ou 'A' for pressionada, diminui a rotação (vira à esquerda)
        # Multiplica por 'et' para garantir movimento consistente independente do FPS
        self.rot += 0.0015 * et * (
            (keys[pg.K_RIGHT] or keys[ord('d')]) - (keys[pg.K_LEFT] or keys[ord('a')])
        )

        # Aceleração com a tecla W (ou seta para cima)
        if keys[pg.K_UP] or keys[ord('w')]:
            if on_border:
                self.vel = 0  # Impede o movimento para frente na borda
            else:
                # Aumenta a velocidade até o máximo permitido
                self.vel = min(self.vel + self.acceleration * et, self.max_speed)

        # Frenagem com a tecla S (ou seta para baixo)
        elif keys[pg.K_DOWN] or keys[ord('s')]:
            if self.vel > 0:
                # Aplica desaceleração de frenagem até parar
                self.vel = max(self.vel - self.brake_deceleration * et, 0)
            else:
                # Aplica desaceleração normal até a velocidade mínima
                self.vel = max(self.vel - self.acceleration * et, self.min_speed)

        # Desaceleração suave quando nem W nem S são pressionados
        else:
            if self.vel > 0:
                # Desacelera naturalmente até parar
                self.vel = max(self.vel - self.deceleration * et, 0)
            elif self.vel < 0:
                # Desacelera naturalmente até parar
                self.vel = min(self.vel + self.deceleration * et, 0)

        # Calcula a nova posição do kart com base na velocidade e direção
        new_posx = self.posx + np.cos(self.rot) * self.vel * et
        new_posy = self.posy + np.sin(self.rot) * self.vel * et

        # Se estiver na borda e tentando avançar, bloqueia o movimento para frente
        if on_border and (keys[pg.K_UP] or keys[ord('w')]):
            self.vel = 0  # Bloqueia avanço na borda
        else:
            # Atualiza a posição do kart com os novos valores
            self.posx = new_posx
            self.posy = new_posy
