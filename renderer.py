import numpy as np
import pygame as pg
from numba import njit

class Renderer:
    def __init__(self, hres, halfvres):
        self.hres, self.halfvres = hres, halfvres
        self.mod = hres / 60
        self.frame = np.random.uniform(0, 1, (hres, halfvres * 2, 3))
        self.load_assets()

    def load_assets(self):
        self.sky = pg.surfarray.array3d(pg.transform.scale(pg.image.load('assets/skybox.jpg'), (360, self.halfvres * 2))) / 255
        self.floor = pg.surfarray.array3d(pg.image.load('assets/MarioKart.png')) / 255
        self.track_surface = pg.surfarray.array3d(pg.image.load('assets/pista.png').convert_alpha()) / 255
        self.border_surface = pg.surfarray.array3d(pg.image.load('assets/borda.png').convert_alpha()) / 255
        self.floor_width, self.floor_height = self.floor.shape[0], self.floor.shape[1]

    def render_frame(self, posx, posy, rot):
        self.frame = new_frame(posx, posy, rot, self.frame, self.sky, self.floor, self.track_surface, self.border_surface, self.hres, self.halfvres, self.mod)
        return pg.surfarray.make_surface(self.frame * 255)

    def is_on_track(self, posx, posy):
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        return np.mean(self.track_surface[xx][yy]) > 0.5

    def is_on_border(self, posx, posy):
        xx, yy = int(posx / 30 % 1 * 1023), int(posy / 30 % 1 * 1023)
        if (yy < 5 or yy > 973) or (xx < 5 or xx > 973):
            return True
        return False

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, track_surface, border_surface, hres, halfvres, mod):
    for i in range(hres):
        rot_i = rot + np.deg2rad(i / mod - 30)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(np.deg2rad(i / mod - 30))
        frame[i][:] = sky[int(np.rad2deg(rot_i) % 359)][:]
        for j in range(halfvres):
            n = (halfvres / (halfvres - j)) / cos2
            x, y = posx + cos * n, posy + sin * n
            xx, yy = int(x / 30 % 1 * 1023), int(y / 30 % 1 * 1023)
            shade = 0.95 + 0.05 * (1 - j / halfvres)
            frame[i][halfvres * 2 - j - 1] = floor[xx][yy] * shade
    return frame
