import pygame as pg
from game import Game

pg.init()

screen_width, screen_height = 800, 600
screen = pg.display.set_mode((screen_width, screen_height))
pg.display.set_caption("Menu")

# Carrega os assets (imagens) necessários para o menu
background = pg.image.load('assets/fundo.png')      # Imagem de fundo do menu
play_button = pg.image.load('assets/play.png')      # Imagem do botão "Play"
exit_button = pg.image.load('assets/exit.png')      # Imagem do botão "Exit"

# Escala os botões
play_button = pg.transform.scale(play_button, (200, 80))
exit_button = pg.transform.scale(exit_button, (200, 80))

# Define as posições dos botões (centralizados na tela)
button_spacing = 20  # Espaçamento vertical entre os botões
play_button_rect = play_button.get_rect(
    center=(
        screen_width // 2,
        screen_height // 2 - (exit_button.get_height() // 2 + button_spacing)
    )
)
exit_button_rect = exit_button.get_rect(
    center=(
        screen_width // 2,
        screen_height // 2 + (play_button.get_height() // 2 + button_spacing)
    )
)

def menu():
    """Exibe a tela de menu principal."""
    running = True
    while running:
        screen.blit(background, (0, 0))

        screen.blit(play_button, play_button_rect)
        screen.blit(exit_button, exit_button_rect)

        # Captura eventos do Pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                if play_button_rect.collidepoint(mouse_pos):
                    Game().run()  # Inicia o jogo chamando o método run da classe Game
                if exit_button_rect.collidepoint(mouse_pos):
                    running = False

        pg.display.update()

if __name__ == '__main__':
    menu()
    pg.quit()