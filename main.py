import pygame as pg
from game import Game

# Inicializa o Pygame
pg.init()

# Define as dimensões da tela
screen_width, screen_height = 800, 600
screen = pg.display.set_mode((screen_width, screen_height))
pg.display.set_caption("Menu")

# Carrega os assets
background = pg.image.load('assets/fundo.png')
play_button = pg.image.load('assets/play.png')
exit_button = pg.image.load('assets/exit.png')

# Escala os botões, caso seja necessário
play_button = pg.transform.scale(play_button, (200, 80))  # Escala o botão play para 200x80
exit_button = pg.transform.scale(exit_button, (200, 80))  # Escala o botão exit para 200x80

# Define as posições dos botões (centralizados)
button_spacing = 20  # Espaçamento entre os botões
play_button_rect = play_button.get_rect(center=(screen_width // 2, screen_height // 2 - (exit_button.get_height() // 2 + button_spacing)))
exit_button_rect = exit_button.get_rect(center=(screen_width // 2, screen_height // 2 + (play_button.get_height() // 2 + button_spacing)))

def menu():
    """Exibe a tela de menu."""
    running = True
    while running:
        # Desenha o fundo
        screen.blit(background, (0, 0))

        # Desenha os botões play e exit
        screen.blit(play_button, play_button_rect)
        screen.blit(exit_button, exit_button_rect)

        # Captura eventos
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                # Detecta se o botão Play foi clicado
                if play_button_rect.collidepoint(pg.mouse.get_pos()):
                    Game().run()  # Inicia o jogo
                # Detecta se o botão Exit foi clicado
                if exit_button_rect.collidepoint(pg.mouse.get_pos()):
                    running = False

        # Atualiza a tela
        pg.display.update()

if __name__ == '__main__':
    menu()  # Chama a tela de menu
    pg.quit()
