import pygame as pg

class SoundManager:
    def __init__(self):
        # Gerencia a música de fundo
        pg.mixer.music.load('assets/nirvana.mp3')
        pg.mixer.music.play(-1)
        #pg.mixer.music.set_volume(0.08)
        pg.mixer.music.set_volume(0.0)
