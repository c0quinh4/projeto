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
        self.slow_down_factor = 0.99           # Fator de redução de velocidade fora da pista
        
    def handle_movement(self, turn_value, accelerate_value, brake_value):
        # Define o fator de velocidade de rotação
        rotation_speed_factor = 0.01  # Ajuste este valor para controlar a sensibilidade
        # Atualiza a rotação proporcionalmente ao valor do eixo
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
        # Se o kart ESTIVER na pista, não aplica redução de velocidade
        if on_track:
            self.vel *= self.slow_down_factor  # Mantém a velocidade normal na pista

        # Calcula a nova posição do kart com base na velocidade e direção
        new_posx = self.posx + np.cos(self.rot) * self.vel * et
        new_posy = self.posy + np.sin(self.rot) * self.vel * et

        # Checar colisão com as paredes
        next_posx = self.posx + np.cos(self.rot) * self.vel * et
        next_posy = self.posy + np.sin(self.rot) * self.vel * et
        if maph[int(next_posx) % size][int(next_posy) % size] != 1:
            # Se não houver parede, atualiza a posição
            self.posx = next_posx
            self.posy = next_posy
        else:
            # Se houver parede, para o kart
            self.vel = 0
