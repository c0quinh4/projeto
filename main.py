import pygame as pg
from game import Game  # Importa a classe Game do módulo game.py

# Inicializa o Pygame
pg.init()

# Define as dimensões da tela
screen_width, screen_height = 800, 600
# Cria a janela do jogo com as dimensões especificadas
screen = pg.display.set_mode((screen_width, screen_height))
# Define o título da janela
pg.display.set_caption("Menu")

# Carrega os assets (imagens) necessários para o menu
background = pg.image.load('assets/fundo.png')      # Imagem de fundo do menu
play_button = pg.image.load('assets/play.png')      # Imagem do botão "Play"
exit_button = pg.image.load('assets/exit.png')      # Imagem do botão "Exit"

# Escala os botões, caso seja necessário
play_button = pg.transform.scale(play_button, (200, 80))  # Redimensiona o botão "Play" para 200x80 pixels
exit_button = pg.transform.scale(exit_button, (200, 80))  # Redimensiona o botão "Exit" para 200x80 pixels

# Define as posições dos botões (centralizados na tela)
button_spacing = 20  # Espaçamento vertical entre os botões
# Calcula a posição do botão "Play" centralizado horizontalmente e acima do centro vertical
play_button_rect = play_button.get_rect(
    center=(
        screen_width // 2,
        screen_height // 2 - (exit_button.get_height() // 2 + button_spacing)
    )
)
# Calcula a posição do botão "Exit" centralizado horizontalmente e abaixo do centro vertical
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
        # Desenha o fundo na tela
        screen.blit(background, (0, 0))

        # Desenha os botões "Play" e "Exit" nas posições calculadas
        screen.blit(play_button, play_button_rect)
        screen.blit(exit_button, exit_button_rect)

        # Captura eventos do Pygame (como cliques e fechamento da janela)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # Se o usuário fechar a janela, encerra o loop do menu
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                # Obtém a posição do mouse no momento do clique
                mouse_pos = pg.mouse.get_pos()
                # Verifica se o botão "Play" foi clicado
                if play_button_rect.collidepoint(mouse_pos):
                    Game().run()  # Inicia o jogo chamando o método run da classe Game
                # Verifica se o botão "Exit" foi clicado
                if exit_button_rect.collidepoint(mouse_pos):
                    running = False  # Sai do loop do menu

        # Atualiza a tela com o que foi desenhado
        pg.display.update()

if __name__ == '__main__':
    menu()  # Chama a função menu para exibir o menu principal
    pg.quit()  # Encerra o Pygame após sair do menu