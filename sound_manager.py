import pygame as pg

class SoundManager:
    def __init__(self):
        # Gerencia a música de fundo
        pg.mixer.music.load('assets/musica.mp3')
        pg.mixer.music.play(-1)
        pg.mixer.music.set_volume(0.08)
