import pygame
from engine import Game
import tkinter as tk
from tkinter import ttk, messagebox
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import seaborn as sns
from PIL import Image, ImageTk
import os

# Initialize pygame
pygame.init()
pygame.font.init()
pygame.display.set_caption("Battleship")

# Global variables
SQ_SIZE = 30
H_MARGIN = SQ_SIZE * 8  # Horizontal margin increased
V_MARGIN = SQ_SIZE * 4  # Vertical margin increased
GRID_SPACING = SQ_SIZE * 2  # Space between grids
WIDTH = SQ_SIZE * 10 * 2 + H_MARGIN + GRID_SPACING
HEIGHT = SQ_SIZE * 10 * 2 + V_MARGIN * 2 + GRID_SPACING
INDENT = 10
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

# Game states
GAME_STATES = {
    "MENU": 0,
    "GAME": 1,
    "GUIDE": 2,
    "AI_SELECT": 3,
    "AI_VS_AI_SELECT": 4
}
current_state = GAME_STATES["MENU"]

# Player settings
HUMAN1 = True
HUMAN2 = False

# AI settings
AI_TYPES = ["random", "bfs", "greedy", "monte_carlo"]
AI_TYPE = "monte_carlo"
AI_TYPE_INDEX = AI_TYPES.index(AI_TYPE)
AI_TYPE2 = "random"  # Default value changed to random
AI_TYPE_INDEX2 = AI_TYPES.index(AI_TYPE2)

# Colors
GREEN = (50, 200, 150)
GREY = (40, 50, 60)
WHITE = (255, 250, 250)
RED = (250, 50, 100)
BLUE = (50, 150, 200)
ORANGE = (250, 140, 20)
BLACK = (0, 0, 0)
DARK_GREY = (30, 30, 30)
LIGHT_GREY = (60, 60, 60)

# Fonts
COLORS = {"U": GREY, "M": BLUE, "H": ORANGE, "S": RED}
titlefont = pygame.font.SysFont("freesansttf", 72)
myfont = pygame.font.SysFont("freesansttf", 40)
smallfont = pygame.font.SysFont("freesansttf", 24)


class Button:
    def __init__(self, x, y, width, height, text, font=myfont, color=WHITE, bg_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.bg_color = bg_color
        self.hovered = False
        self._text_surface = self.font.render(self.text, True, self.color)
        self._text_rect = self._text_surface.get_rect(center=self.rect.center)

    def draw(self):
        if self.bg_color:
            pygame.draw.rect(SCREEN, self.bg_color, self.rect, border_radius=5)

        if self.hovered:
            pygame.draw.rect(SCREEN, ORANGE, self.rect, 2, border_radius=5)
            glow = self.font.render(self.text, True, ORANGE)
        else:
            pygame.draw.rect(SCREEN, self.color, self.rect, 2, border_radius=5)
            glow = self._text_surface

        SCREEN.blit(glow, self._text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


def draw_menu():
    """Draws the main menu"""
    # Title
    title = titlefont.render("BATTLESHIP", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH // 2, 100))
    SCREEN.blit(title, title_rect)

    # Menu buttons
    buttons = [
        Button(WIDTH // 2 - 150, 220, 300, 60, "PLAYER vs AI", bg_color=DARK_GREY),
        Button(WIDTH // 2 - 150, 300, 300, 60, "AI vs AI", bg_color=DARK_GREY),
        Button(WIDTH // 2 - 150, 380, 300, 60, "AI GUIDE", bg_color=DARK_GREY),
        Button(WIDTH // 2 - 150, 460, 300, 60, "EXIT", bg_color=DARK_GREY)
    ]

    for button in buttons:
        button.draw()

    return buttons


def draw_grid(player, left=0, top=0, search=False):
    """Oyun tahtasını çizer"""
    try:
        for i in range(100):
            x = left + (i % 10) * SQ_SIZE
            y = top + (i // 10) * SQ_SIZE
            square = pygame.Rect(x, y, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(SCREEN, WHITE, square, width=2)
            
            if search and player and player.search:
                pygame.draw.circle(SCREEN, COLORS[player.search[i]], (x + SQ_SIZE // 2, y + SQ_SIZE // 2), SQ_SIZE // 4)
    except Exception as e:
        print(f"Grid çizim hatası: {e}")


def draw_ships(player, left=0, top=0):
    """Gemileri çizer"""
    try:
        if player and player.ships:
            for ship in player.ships:
                x = left + ship.col * SQ_SIZE + INDENT
                y = top + ship.row * SQ_SIZE + INDENT
                width = ship.size * SQ_SIZE - 2 * INDENT if ship.orientation == "h" else SQ_SIZE - 2 * INDENT
                height = SQ_SIZE - 2 * INDENT if ship.orientation == "h" else ship.size * SQ_SIZE - 2 * INDENT
                pygame.draw.rect(SCREEN, GREEN, pygame.Rect(x, y, width, height), border_radius=10)
    except Exception as e:
        print(f"Gemi çizim hatası: {e}")


def draw_guide():
    """Draws the AI guide"""
    # Title
    title = titlefont.render("AI GUIDE", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH // 2, 60))
    SCREEN.blit(title, title_rect)

    # AI types and descriptions
    ai_info = [
        ("RANDOM AI", "The simplest AI type. Makes random shots. Ideal for beginners."),
        ("BFS AI", "Searches around when it finds a ship. Makes logical moves."),
        ("MONTE CARLO AI", "The most advanced AI. Calculates probabilities and selects the best move. A tough opponent.")
    ]

    y = 140
    for ai_type, description in ai_info:
        # AI type
        type_text = myfont.render(ai_type, True, ORANGE)
        SCREEN.blit(type_text, (50, y))

        # Description
        desc_text = smallfont.render(description, True, WHITE)
        SCREEN.blit(desc_text, (50, y + 40))

        y += 100

    # Heatmap example for Monte Carlo AI
    if os.path.exists('monte_carlo_heatmap.png'):
        try:
            # Load and display heatmap image
            heatmap_img = pygame.image.load('monte_carlo_heatmap.png')
            # Scale the image to fit
            heatmap_img = pygame.transform.scale(heatmap_img, (200, 200))
            # Position the heatmap
            SCREEN.blit(heatmap_img, (WIDTH - 250, 200))
            
            # Add heatmap description
            heatmap_desc = smallfont.render("Monte Carlo AI's probability heatmap", True, WHITE)
            SCREEN.blit(heatmap_desc, (WIDTH - 250, 180))
        except Exception as e:
            print(f"Heatmap loading error: {e}")

    # Bottom info
    info_text = "Each AI type offers a different difficulty level. In AI vs AI mode, you can compare two different AIs."
    info_surface = smallfont.render(info_text, True, LIGHT_GREY)
    info_rect = info_surface.get_rect(center=(WIDTH // 2, HEIGHT - 120))
    SCREEN.blit(info_surface, info_rect)

    # Back button
    back_button = Button(WIDTH // 2 - 100, HEIGHT - 80, 200, 50, "BACK", bg_color=DARK_GREY)
    back_button.draw()

    return [back_button]


def draw_ai_select():
    """Draws the AI selection screen"""
    # Title
    title = titlefont.render("SELECT AI TYPE", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH // 2, 60))
    SCREEN.blit(title, title_rect)

    # Panel background
    panel = pygame.Rect(WIDTH // 2 - 200, 100, 400, HEIGHT - 200)
    pygame.draw.rect(SCREEN, DARK_GREY, panel, border_radius=10)

    buttons = []
    y = 150
    for i, ai_type in enumerate(AI_TYPES):
        button = Button(WIDTH // 2 - 150, y, 300, 50, ai_type.upper(), bg_color=DARK_GREY)
        button.draw()
        buttons.append(button)
        y += 70

    # Back button - moved up
    back_button = Button(WIDTH // 2 - 100, y + 20, 200, 50, "BACK", bg_color=DARK_GREY)
    back_button.draw()
    buttons.append(back_button)

    return buttons


def draw_ai_vs_ai_select():
    """Draws the AI vs AI selection screen"""
    # Title
    title = titlefont.render("SELECT AI TYPES", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH // 2, 60))
    SCREEN.blit(title, title_rect)

    # Left panel (AI 1)
    panel1 = pygame.Rect(WIDTH // 4 - 150, 100, 300, HEIGHT - 350)  # Panel yüksekliğini azalttım
    pygame.draw.rect(SCREEN, DARK_GREY, panel1, border_radius=10)

    # Right panel (AI 2)
    panel2 = pygame.Rect(3 * WIDTH // 4 - 150, 100, 300, HEIGHT - 350)  # Panel yüksekliğini azalttım
    pygame.draw.rect(SCREEN, DARK_GREY, panel2, border_radius=10)

    buttons = []
    
    # AI 1 selection
    ai1_text = myfont.render("AI 1:", True, WHITE)
    SCREEN.blit(ai1_text, (WIDTH // 4 - 130, 120))
    
    y = 170
    for i, ai_type in enumerate(AI_TYPES):
        button = Button(WIDTH // 4 - 130, y, 260, 50, ai_type.upper(), bg_color=DARK_GREY)
        button.draw()
        buttons.append(button)
        y += 70

    # AI 2 selection
    ai2_text = myfont.render("AI 2:", True, WHITE)
    SCREEN.blit(ai2_text, (3 * WIDTH // 4 - 130, 120))
    
    y = 170
    for i, ai_type in enumerate(AI_TYPES):
        button = Button(3 * WIDTH // 4 - 130, y, 260, 50, ai_type.upper(), bg_color=DARK_GREY)
        button.draw()
        buttons.append(button)
        y += 70

    # Start ve Back butonlarını yukarı çektim
    start_button = Button(WIDTH // 2 - 100, HEIGHT - 200, 200, 50, "START", bg_color=DARK_GREY)
    start_button.draw()
    buttons.append(start_button)

    back_button = Button(WIDTH // 2 - 100, HEIGHT - 140, 200, 50, "BACK", bg_color=DARK_GREY)
    back_button.draw()
    buttons.append(back_button)

    return buttons


def main():
    global current_state, game, AI_TYPE, AI_TYPE_INDEX, AI_TYPE2, AI_TYPE_INDEX2, HUMAN1, HUMAN2

    game = None
    pausing = False
    last_ai_move_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    game_type = None
    buttons = []

    # Create initial heatmap for guide
    if not os.path.exists('monte_carlo_heatmap.png'):
        try:
            from engine import Game
            temp_game = Game(False, False, ai_type="monte_carlo")
            temp_game.create_heatmap([0]*100, ["U"]*100)
        except Exception as e:
            print(f"Heatmap creation error: {e}")

    while True:
        try:
            current_time = pygame.time.get_ticks()
            SCREEN.fill(BLACK)

            # Mevcut ekranı çiz
            if current_state == GAME_STATES["MENU"]:
                buttons = draw_menu()
            elif current_state == GAME_STATES["AI_SELECT"]:
                buttons = draw_ai_select()
            elif current_state == GAME_STATES["AI_VS_AI_SELECT"]:
                buttons = draw_ai_vs_ai_select()
            elif current_state == GAME_STATES["GUIDE"]:
                buttons = draw_guide()
            elif current_state == GAME_STATES["GAME"] and game:
                # Oyun ekranını çiz
                # Sol üst grid (Oyuncu 1'in atış tahtası)
                draw_grid(game.player2, left=H_MARGIN // 2, top=V_MARGIN, search=True)

                # Sol alt grid (Oyuncu 1'in gemileri)
                draw_grid(game.player1, left=H_MARGIN // 2, top=HEIGHT - V_MARGIN - SQ_SIZE * 10 - GRID_SPACING)
                draw_ships(game.player1, left=H_MARGIN // 2, top=HEIGHT - V_MARGIN - SQ_SIZE * 10 - GRID_SPACING)

                # Sağ üst grid (Oyuncu 2'nin atış tahtası)
                draw_grid(game.player1, left=WIDTH - H_MARGIN // 2 - SQ_SIZE * 10, top=V_MARGIN, search=True)

                # Sağ alt grid (Oyuncu 2'nin gemileri)
                draw_grid(game.player2, left=WIDTH - H_MARGIN // 2 - SQ_SIZE * 10,
                          top=HEIGHT - V_MARGIN - SQ_SIZE * 10 - GRID_SPACING)
                draw_ships(game.player2, left=WIDTH - H_MARGIN // 2 - SQ_SIZE * 10,
                           top=HEIGHT - V_MARGIN - SQ_SIZE * 10 - GRID_SPACING)

                # Oyuncu panelleri
                # Sol panel (Oyuncu 1)

                panel_height = 60  # Yükseklik sabitlendi
                panel_top = V_MARGIN - panel_height - 10  # Gridin tam üstüne gelsin

                player1_panel = pygame.Rect(H_MARGIN // 2 - 10, panel_top, SQ_SIZE * 10 + 20, panel_height)

                pygame.draw.rect(SCREEN, DARK_GREY, player1_panel, border_radius=10)

                # Sağ panel (Oyuncu 2)
                player2_panel = pygame.Rect(WIDTH - H_MARGIN // 2 - SQ_SIZE * 10 - 10, panel_top, SQ_SIZE * 10 + 20,
                                            panel_height)
                pygame.draw.rect(SCREEN, DARK_GREY, player2_panel, border_radius=10)

                # Player names
                player1_text = "PLAYER 1" if game.human1 else f"AI 1 ({AI_TYPE})"
                player2_text = "PLAYER 2" if game.human2 else (
                    f"AI 2 ({AI_TYPE2})" if not game.human1 and not game.human2 else f"AI 2 ({AI_TYPE})")

                player1_surface = myfont.render(player1_text, True, WHITE)
                player2_surface = myfont.render(player2_text, True, WHITE)

                player1_rect = player1_surface.get_rect(
                    center=(H_MARGIN // 2 + SQ_SIZE * 5, panel_top + panel_height // 2))
                player2_rect = player2_surface.get_rect(
                    center=(WIDTH - H_MARGIN // 2 - SQ_SIZE * 5, panel_top + panel_height // 2))

                SCREEN.blit(player1_surface, player1_rect)
                SCREEN.blit(player2_surface, player2_rect)

                # Turn indicator
                current_player = "1" if game.player1_turn else "2"
                turn_text = f"TURN: PLAYER {current_player}"
                turn_surface = myfont.render(turn_text, True, ORANGE)
                turn_rect = turn_surface.get_rect(center=(WIDTH // 2, HEIGHT - V_MARGIN // 2))
                SCREEN.blit(turn_surface, turn_rect)

                # Grid titles
                # Left top
                # attack_title1 = smallfont.render("ATTACK BOARD", True, WHITE)
                # attack_rect1 = attack_title1.get_rect(center=(H_MARGIN//2 + SQ_SIZE * 1, V_MARGIN - 40))
                # SCREEN.blit(attack_title1, attack_rect1)

                # Left bottom
                # ship_title1 = smallfont.render("SHIP BOARD", True, WHITE)
                # ship_rect1 = ship_title1.get_rect(center=(H_MARGIN//2 + SQ_SIZE * 1, HEIGHT - V_MARGIN - SQ_SIZE * 10 - GRID_SPACING - 40))
                # SCREEN.blit(ship_title1, ship_rect1)

                # Right top
                # attack_title2 = smallfont.render("ATTACK BOARD", True, WHITE)
                # attack_rect2 = attack_title2.get_rect(center=(WIDTH - H_MARGIN//2 - SQ_SIZE * 1, V_MARGIN - 40))
                # SCREEN.blit(attack_title2, attack_rect2)

                # Right bottom
                # ship_title2 = smallfont.render("SHIP BOARD", True, WHITE)
                # ship_rect2 = ship_title2.get_rect(center=(WIDTH - H_MARGIN//2 - SQ_SIZE * 1, HEIGHT - V_MARGIN - SQ_SIZE * 10 - GRID_SPACING - 40))
                # SCREEN.blit(ship_title2, ship_rect2)

                # Bottom control panel
                controls_panel = pygame.Rect(0, HEIGHT - V_MARGIN // 2 - 20, WIDTH, V_MARGIN // 2)
                pygame.draw.rect(SCREEN, DARK_GREY, controls_panel)

                controls = "SPACE - Pause  |  RETURN - New Game  |  ESC - Menu"
                controls_surface = smallfont.render(controls, True, WHITE)
                controls_rect = controls_surface.get_rect(center=(WIDTH // 2, HEIGHT - V_MARGIN // 4))
                SCREEN.blit(controls_surface, controls_rect)

                # Info bars
                info_bg = pygame.Rect(0, 0, WIDTH, 35)
                pygame.draw.rect(SCREEN, DARK_GREY, info_bg)

                if game_type == "aivai":
                    ai_text = f"AI1: {AI_TYPE} vs AI2: {AI_TYPE2}"
                else:
                    ai_text = f"PLAYER vs {AI_TYPE} AI"
                ai_surface = smallfont.render(ai_text, True, WHITE)
                SCREEN.blit(ai_surface, (20, 10))

                status = "PAUSED" if pausing else "RUNNING"
                status_text = f"Status: {status}"
                status_surface = smallfont.render(status_text, True, WHITE)
                SCREEN.blit(status_surface, (WIDTH // 2 - 50, 10))

                # AI move
                if not pausing and not game.over:
                    if ((game.player1_turn and not game.human1) or (not game.player1_turn and not game.human2)) and \
                            (current_time - last_ai_move_time >= 500):
                        try:
                            game.ai_move()
                            last_ai_move_time = current_time
                        except Exception as e:
                            print(f"AI Move Error: {e}")

                # Game over screen
                if game.over:
                    overlay = pygame.Surface((WIDTH, HEIGHT))
                    overlay.fill(BLACK)
                    overlay.set_alpha(128)
                    SCREEN.blit(overlay, (0, 0))

                    text = f"GAME OVER - PLAYER {game.result} WINS!"
                    new_game_text = "Press RETURN for a new game"

                    text_surface = myfont.render(text, True, WHITE)
                    new_game_surface = smallfont.render(new_game_text, True, WHITE)

                    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                    new_game_rect = new_game_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

                    SCREEN.blit(text_surface, text_rect)
                    SCREEN.blit(new_game_surface, new_game_rect)

            # Olayları işle
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if current_state == GAME_STATES["MENU"]:
                        for i, button in enumerate(buttons):
                            if button.handle_event(event):
                                if i == 0:  # Player vs AI
                                    current_state = GAME_STATES["AI_SELECT"]
                                    game_type = "pvai"
                                elif i == 1:  # AI vs AI
                                    current_state = GAME_STATES["AI_VS_AI_SELECT"]
                                    game_type = "aivai"
                                elif i == 2:  # AI Rehberi
                                    current_state = GAME_STATES["GUIDE"]
                                elif i == 3:  # Çıkış
                                    return

                    elif current_state == GAME_STATES["AI_SELECT"]:
                        for i, button in enumerate(buttons):
                            if button.handle_event(event):
                                if i < len(AI_TYPES):  # AI tipi seçildi
                                    AI_TYPE = AI_TYPES[i]
                                    AI_TYPE_INDEX = i
                                    HUMAN1, HUMAN2 = True, False
                                    game = Game(HUMAN1, HUMAN2, ai_type=AI_TYPE)
                                    current_state = GAME_STATES["GAME"]
                                else:  # Geri butonu
                                    current_state = GAME_STATES["MENU"]

                    elif current_state == GAME_STATES["AI_VS_AI_SELECT"]:
                        for i, button in enumerate(buttons):
                            if button.handle_event(event):
                                if i < len(AI_TYPES):  # Birinci AI seçimi
                                    AI_TYPE = AI_TYPES[i]
                                    AI_TYPE_INDEX = i
                                    game_type = "aivai"  # AI vs AI modunu ayarla
                                elif i >= len(AI_TYPES) and i < len(AI_TYPES) * 2:  # İkinci AI seçimi
                                    ai2_index = i - len(AI_TYPES)
                                    AI_TYPE2 = AI_TYPES[ai2_index]
                                    AI_TYPE_INDEX2 = ai2_index
                                    game_type = "aivai"  # AI vs AI modunu ayarla
                                elif i == len(buttons) - 2:  # Başlat butonu
                                    if game_type == "aivai":  # Sadece AI vs AI modunda
                                        HUMAN1, HUMAN2 = False, False
                                        game = Game(HUMAN1, HUMAN2, ai_type=AI_TYPE, ai_type2=AI_TYPE2)
                                        current_state = GAME_STATES["GAME"]
                                else:  # Geri butonu
                                    current_state = GAME_STATES["MENU"]

                    elif current_state == GAME_STATES["GUIDE"]:
                        for button in buttons:
                            if button.handle_event(event):
                                current_state = GAME_STATES["MENU"]

                    elif current_state == GAME_STATES["GAME"] and game and game.human1 and game.player1_turn:
                        # İnsan oyuncunun hamlesi
                        x, y = pygame.mouse.get_pos()
                        grid_x = x - (WIDTH - H_MARGIN // 2 - SQ_SIZE * 10)  # Sağ üst grid için x koordinatı
                        grid_y = y - V_MARGIN  # Üst grid için y koordinatı

                        # Sağ üst grid için kontrol (Oyuncu 1'in atış tahtası)
                        if (0 <= grid_x <= SQ_SIZE * 10) and (0 <= grid_y <= SQ_SIZE * 10):
                            row = grid_y // SQ_SIZE
                            col = grid_x // SQ_SIZE
                            game.make_move(row, col)

                elif event.type == pygame.KEYDOWN:
                    if current_state == GAME_STATES["GAME"]:
                        if event.key == pygame.K_ESCAPE:
                            current_state = GAME_STATES["MENU"]
                            game = None
                        elif event.key == pygame.K_SPACE:
                            pausing = not pausing
                        elif event.key == pygame.K_RETURN:
                            if game_type == "aivai":
                                game = Game(HUMAN1, HUMAN2, ai_type=AI_TYPE, ai_type2=AI_TYPE2)
                            else:
                                game = Game(HUMAN1, HUMAN2, ai_type=AI_TYPE)
                            last_ai_move_time = current_time

            pygame.display.flip()
            clock.tick(60)

        except Exception as e:
            print(f"Ana döngü hatası: {e}")
            continue


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Program hatası: {e}")
    finally:
        pygame.quit()
