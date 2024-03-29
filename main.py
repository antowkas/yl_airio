import pygame
from models import MainWindow
from single_objects import (
    all_sprites
)

pygame.font.init()
pygame.init()

size = width, height = 1000, 800
screen = pygame.display.set_mode(size)

clock = pygame.time.Clock()
running = True
FPS = 60

active_window = MainWindow(window_width=width, window_height=height,
                           dot_size=64)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                active_window.restart()

    all_sprites.update()
    screen.fill((32, 32, 32))
    all_sprites.draw(screen)
    pygame.display.flip()

    active_window = active_window.next_window()

    clock.tick(FPS)
