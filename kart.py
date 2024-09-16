import numpy as np
import pygame as pg

class Kart:
    def __init__(self):
        self.posx, self.posy, self.rot, self.vel = 27, 18.5, 4.7, 0  # Posição inicial ajustada
        self.acceleration = 0.00001
        self.deceleration = 0.00001
        self.brake_deceleration = 0.0003
        self.max_speed = 0.01
        self.min_speed = -0.005
        self.slow_down_factor = 0.8  # Redução de velocidade fora da pista

    def update(self, keys, et, on_track, on_border):
        # Se o kart ESTIVER na pista, não faz a redução de velocidade
        if on_track:
            self.vel *= self.slow_down_factor  # Mantém a velocidade normal na pista

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

        # Se estiver na borda, o kart pode se mover para trás ou para os lados
        if on_border and (keys[pg.K_UP] or keys[ord('w')]):  # Bloqueia avanço na borda
            self.vel = 0
        else:
            self.posx = new_posx
            self.posy = new_posy
