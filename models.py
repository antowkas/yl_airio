from datetime import datetime
from typing import Iterable

import pygame
from pygame.font import Font
from pygame.sprite import Sprite

from single_objects import (
    all_sprites, wall_sprites,
    player_sprites, button_sprites,
    gate_sprites, win_sprites,
    active_player_id, number_players,
)
from pg_utilities import (
    normalize_vector, flatten,
    read_bin_level_data,
    button_color, player_color,
)
from pygame.locals import (
    K_w, K_UP,
    K_a, K_LEFT,
    K_s, K_DOWN,
    K_d, K_RIGHT,
    K_LSHIFT, K_RSHIFT,
    K_TAB
)


# 0x00       | Empty     | +
# 0x01       | Wall      | +
# 0x02       | OR  Win   | ?
# 0x03       | AND Win   | -
# 0x10..0x1F | Buttons   | +
# 0x20..0x2F | OR  Gates | +
# 0x30..0x3F | AND Gates | +
# 0xF0..0xF7 | Players   | +

class Wall(Sprite):
    def __init__(self, x, y, size=64, fill_color="white"):
        super().__init__(all_sprites)
        self.add(wall_sprites)
        self.image = pygame.Surface((size, size),
                                    pygame.SRCALPHA, 32)
        pygame.draw.rect(self.image, fill_color,
                         (0, 0, size, size))
        self.rect = pygame.Rect(x, y, size, size)


class Gate(Sprite):
    def __init__(self, x, y, size=64, gate_id=0, type_or=True):
        super().__init__(all_sprites)
        self.add(gate_sprites)

        self.gate_id = gate_id
        self.size = size
        self.type_or = type_or
        self.active = False
        self.disable()

        self.image = pygame.Surface((size, size),
                                    pygame.SRCALPHA, 32)
        self.image_update()
        self.rect = pygame.Rect(x, y, size, size)

    def disable(self):
        self.add(wall_sprites)
        self.active = False

    def enable(self):
        wall_sprites.remove(self)
        self.active = True

    def logic_update(self):
        active = (all, any)[self.type_or](map(lambda button: button.active,
                                              filter(lambda button: button.button_id == self.gate_id, button_sprites)))
        if self.active != active:
            if active:
                self.enable()
            else:
                self.disable()
        self.image_update()

    def image_update(self):
        self.image.fill(pygame.SRCALPHA)
        pygame.draw.rect(self.image, button_color(self.gate_id, self.active is False),
                         (0, 0, self.size, self.size), self.size // 8)
        if self.active:
            pygame.draw.rect(self.image, pygame.SRCALPHA,
                             (self.size // 4, 0, self.size // 8, self.size), self.size // 8)
            pygame.draw.rect(self.image, pygame.SRCALPHA,
                             (self.size * 0.625, 0, self.size // 8, self.size), self.size // 8)
            pygame.draw.rect(self.image, pygame.SRCALPHA,
                             (0, self.size // 4, self.size, self.size // 8), self.size // 8)
            pygame.draw.rect(self.image, pygame.SRCALPHA,
                             (0, self.size * 0.625, self.size, self.size // 8), self.size // 8)
        if not self.type_or:
            pygame.draw.rect(self.image, button_color(self.gate_id, self.active is False),
                             (self.size // 4, self.size // 4, self.size // 2, self.size // 2), self.size // 8)


class Button(Sprite):
    def __init__(self, x, y, size=32, button_id=0):
        super().__init__(all_sprites)
        self.add(button_sprites)

        self.button_id = button_id
        self.size = size
        self.active = False

        self.image = pygame.Surface((size, size),
                                    pygame.SRCALPHA, 32)
        self.image_update()
        self.rect = pygame.Rect(x, y, size, size)

    def update(self):
        self.collide()

    def image_update(self):
        self.image.fill(pygame.SRCALPHA)
        pygame.draw.rect(self.image, button_color(self.button_id, self.active),
                         (0, 0, self.size, self.size), self.size // 4)

    def collide(self):
        active = self.active
        if pygame.sprite.spritecollideany(self, player_sprites):
            self.active = True
            self.image_update()
        else:
            self.active = False
            self.image_update()
        if active != self.active:
            for gate in gate_sprites:
                gate.logic_update()


class Win(Sprite):
    def __init__(self, x, y, size=80, type_and=True, font: Font = None, win_callbacks: Iterable = None):
        super().__init__(all_sprites)
        self.add(win_sprites)

        if win_callbacks is None:
            win_callbacks = []
        self.win_callbacks = win_callbacks

        if font is None:
            self.font = Font('data/fonts/BrassMono-Regular.ttf', size // 2)

        self.type_and = type_and
        self.size = size
        self.players = 0
        self.color = (127, 255, 127, 204)
        self.is_win = False

        self.image = pygame.Surface((size, size),
                                    pygame.SRCALPHA, 32)
        self.image_update()
        self.rect = pygame.Rect(x, y, size, size)

    def update(self):
        self.collide()

    def image_update(self):
        self.image.fill(pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color,
                         (0, 0, self.size, self.size))

        text_surface = self.font.render(f'{self.players}/{int(number_players)}', True, (32, 32, 32))
        self.image.blit(text_surface, ((self.size - text_surface.get_size()[0]) // 2,
                                       (self.size - text_surface.get_size()[1]) // 1.75))

    def win(self):
        for callback in self.win_callbacks:
            callback()

    def collide(self):
        players = sum(map(lambda player: self.rect.colliderect(player.rect), player_sprites))
        if players != self.players:
            self.players = players
            self.image_update()
            if self.type_and and self.players == int(number_players):
                self.win()
            elif not self.type_and and self.players > 0:
                self.win()


class Player(Sprite):
    def __init__(self, x, y, size=48, player_id=0, base_speed=6):
        super().__init__(all_sprites)
        self.add(player_sprites)

        self.player_id = player_id

        self.base_speed = base_speed
        self.speed = base_speed

        self.image = pygame.Surface((size, size),
                                    pygame.SRCALPHA, 32)
        pygame.draw.rect(self.image, player_color(player_id),
                         (0, 0, size, size))
        self.rect = pygame.Rect(x, y, size, size)

    def update(self):
        if int(active_player_id) == self.player_id:
            vx, vy = self.get_input_vectors()
            if self.is_shift_pressed():
                self.speed = self.base_speed * 2
            else:
                self.speed = self.base_speed
            self.move_and_collide(vx, vy)

    @staticmethod
    def is_shift_pressed():
        keys = pygame.key.get_pressed()
        return keys[K_LSHIFT] or keys[K_RSHIFT]

    @staticmethod
    def get_input_vectors():
        keys = pygame.key.get_pressed()
        vx, vy = 0, 0
        if keys[K_w] or keys[K_UP]:
            vy += -1
        if keys[K_a] or keys[K_LEFT]:
            vx += -1
        if keys[K_s] or keys[K_DOWN]:
            vy += 1
        if keys[K_d] or keys[K_RIGHT]:
            vx += 1
        return normalize_vector((vx, vy))

    def move(self, vx, vy, speed=None):
        if speed is None:
            speed = self.speed
        self.rect.x = self.rect.x + vx * speed
        self.rect.y = self.rect.y + vy * speed

    def move_and_collide(self, vx, vy):
        fx, fy = True, True

        if pygame.sprite.spritecollideany(self, wall_sprites):
            return False

        if pygame.sprite.spritecollideany(self,
                                          filter(lambda x: int(active_player_id) != x.player_id, player_sprites)):
            self.speed *= 0.5

        if vx:
            self.move(vx, 0)
            if pygame.sprite.spritecollideany(self, wall_sprites):
                fx = False
                while pygame.sprite.spritecollideany(self, wall_sprites):
                    self.move(-vx, 0, speed=1)
        if vy:
            self.move(0, vy)
            if pygame.sprite.spritecollideany(self, wall_sprites):
                fy = False
                while pygame.sprite.spritecollideany(self, wall_sprites):
                    self.move(0, -vy, speed=1)

        return fx or fy


class GameTimer(Sprite):
    def __init__(self, x, y, size=64, font: Font = None):
        super().__init__(all_sprites)
        self.size = size
        self.start_time = datetime.now()

        if font is None:
            self.font = Font('data/fonts/BrassMono-Regular.ttf', size // 2)

        self.image = pygame.Surface((size * 10, size),
                                    pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(x, y, size * 10, size)

    def update(self):
        self.image_update()

    def get_time(self):
        return datetime.now() - self.start_time

    def image_update(self):
        color = "white"
        self.image.fill(pygame.SRCALPHA)
        text_surface = self.font.render(f'{self.get_time().total_seconds():.2f} seconds', True,
                                        color)

        self.image.blit(text_surface, (self.size * 0.25,
                                       (self.size - text_surface.get_size()[1]) // 1.75))


class CurrentPlayer(Sprite):
    def __init__(self, x, y, size=64, font: Font = None):
        super().__init__(all_sprites)
        self.size = size

        if font is None:
            self.font = Font('data/fonts/BrassMono-Regular.ttf', size // 2)

        self.last_active_player = None
        self.tab_pressed = False

        self.image = pygame.Surface((size * 10, size),
                                    pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(x, y, size * 10, size)

    def is_tab_down(self):
        keys = pygame.key.get_pressed()
        if self.tab_pressed:
            self.tab_pressed = keys[K_TAB]
            return False
        else:
            self.tab_pressed = keys[K_TAB]
            return keys[K_TAB]

    def update(self):
        if int(active_player_id) != self.last_active_player:
            self.last_active_player = int(active_player_id)
            self.image_update()
        if self.is_tab_down():
            active_player_id.set((int(active_player_id) + 1) % int(number_players))

    def image_update(self):
        color = player_color(self.last_active_player)
        self.image.fill(pygame.SRCALPHA)
        pygame.draw.rect(self.image, color,
                         (0, 0, self.size * 4, self.size), 8)
        text_surface = self.font.render(f'Player {self.last_active_player + 1}/{int(number_players)}', True, color)
        self.image.blit(text_surface, ((self.size * 4 - text_surface.get_size()[0]) // 2,
                                       (self.size - text_surface.get_size()[1]) // 1.75))

        text_surface = self.font.render('Use TAB to switch', True, color)
        self.image.blit(text_surface, (self.size * 4.5,
                                       (self.size - text_surface.get_size()[1]) // 1.75))


class StatisticSprite(Sprite):
    def __init__(self, x, y, size=64, font: Font = None, **statistics):
        super().__init__(all_sprites)
        self.size = size
        self.statistics = statistics

        if font is None:
            font = Font('data/fonts/BrassMono-Regular.ttf', size // 2)
        self.font = font

        self.image = pygame.Surface((size * 10, size * 10),
                                    pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(x, y, size * 10, size * 10)
        self.image_update()

    def image_update(self):
        color = (255, 255, 255)
        self.image.fill(pygame.SRCALPHA)
        pygame.draw.rect(self.image, (*color, 10),
                         (0, 0, self.size * 10, self.size * 10), )
        pygame.draw.rect(self.image, color,
                         (0, 0, self.size * 10, self.size * 10), 8)
        text = "\n".join(map(lambda item: f"{item[0]} - {item[1]}", self.statistics.items()))

        for i, line in enumerate(text.split("\n"), start=3):
            text_surface = self.font.render(line, True, color)
            self.image.blit(text_surface, ((self.size * 10 - text_surface.get_size()[0]) // 2,
                                           (self.size * (i + 1) - text_surface.get_size()[1]) // 1.75))

        text_surface = self.font.render('You have won!', True, (100, 255, 100))
        self.image.blit(text_surface, ((self.size * 10 - text_surface.get_size()[0]) // 2,
                                       (self.size * 2 - text_surface.get_size()[1]) // 1.75))


class TextButton(Sprite):
    def __init__(self, x, y, text, size=64, font: Font = None, callbacks=None):
        super().__init__(all_sprites)
        self.size = size
        self.text = text

        if callbacks is None:
            callbacks = []
        self.callbacks = callbacks

        if font is None:
            font = Font('data/fonts/BrassMono-Regular.ttf', size // 2)
        self.font = font

        self.image = pygame.Surface((size * 6, size * 2),
                                    pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(x, y, size * 6, size * 2)
        self.image_update()

    def pressed(self):
        for callback in self.callbacks:
            callback()

    def update(self):
        self.get_input()

    def get_input(self):
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                self.pressed()

    def image_update(self):
        color = (100, 240, 100)
        self.image.fill(pygame.SRCALPHA)
        pygame.draw.rect(self.image, (*color, 50),
                         (0, 0, self.size * 6, self.size * 2))
        pygame.draw.rect(self.image, color,
                         (0, 0, self.size * 6, self.size * 2), 8)

        text_surface = self.font.render(self.text, True, color)
        self.image.blit(text_surface, ((self.size * 6 - text_surface.get_size()[0]) // 2,
                                       (self.size * 2 - text_surface.get_size()[1]) // 2))


class MainWindow:
    def __init__(self, dot_size=64, window_width=None, window_height=None):
        self.switch_window = None
        self.sprites = []
        self.dot_size = dot_size
        self.window_width = window_width
        self.window_height = window_height

        self.width_indent = (window_width - dot_size * 10) // 2
        self.height_indent = (window_height - dot_size * 10) // 2

        self.load_sprites()

    def load_sprites(self):
        self.sprites.append(TextButton(self.width_indent + self.dot_size * (-2),
                                       self.height_indent + self.dot_size * 0, "Level 1",
                                       callbacks=(lambda: self.switch("data/levels/test_level.bin"),)))
        self.sprites.append(TextButton(self.width_indent + self.dot_size * 6,
                                       self.height_indent + self.dot_size * 0, "Level 2",
                                       callbacks=(lambda: self.switch("data/levels/level2.bin"),)))
        self.sprites.append(TextButton(self.width_indent + self.dot_size * (-2),
                                       self.height_indent + self.dot_size * 3, "Level 3",
                                       callbacks=(lambda: self.switch("data/levels/level3.bin"),)))
        self.sprites.append(TextButton(self.width_indent + self.dot_size * 6,
                                       self.height_indent + self.dot_size * 3, "Level 4",
                                       callbacks=(lambda: self.switch("data/levels/level4.bin"),)))

    def switch(self, path):
        self.switch_window = LevelWindow(path,
                                         window_width=self.window_width, window_height=self.window_height,
                                         dot_size=64)

    def __del__(self):
        self.kill_sprites()

    def kill_sprites(self):
        for sprite in self.sprites:
            sprite.kill()

    def restart(self):
        self.kill_sprites()
        self.load_sprites()

    def next_window(self):
        if self.switch_window is not None:
            next_wind = self.switch_window
            self.kill_sprites()
            return next_wind
        return self


class StatisticsWindow:
    def __init__(self, dot_size=64, window_width=None, window_height=None, **statistics):
        self.switch_window = False
        self.sprites = []
        self.dot_size = dot_size
        self.window_width = window_width
        self.window_height = window_height
        self.statistics = statistics

        self.width_indent = (window_width - dot_size * 10) // 2
        self.height_indent = (window_height - dot_size * 10) // 2

        self.load_sprites()

    def load_sprites(self):
        self.sprites.append(StatisticSprite(self.width_indent, self.height_indent,
                                            self.dot_size, **self.statistics))
        self.sprites.append(TextButton(self.width_indent + self.dot_size * 2,
                                       self.height_indent + self.dot_size * 7, "Back to main menu",
                                       callbacks=(self.button_pressed,)))

    def button_pressed(self):
        self.switch_window = True

    def __del__(self):
        self.kill_sprites()

    def kill_sprites(self):
        for sprite in self.sprites:
            sprite.kill()

    def restart(self):
        self.kill_sprites()
        self.load_sprites()

    def next_window(self):
        if self.switch_window:
            next_wind = MainWindow(window_width=self.window_width, window_height=self.window_height,
                                   dot_size=64)
            self.kill_sprites()
            return next_wind
        return self


class LevelWindow:
    def __init__(self, path, dot_size=64, window_width=800, window_height=800):
        self.level = read_bin_level_data(path)
        self.path = path
        self.level_width, self.level_height = len(self.level[0]), len(self.level)
        self.sprites = []
        self.dot_size = dot_size
        self.window_width = window_width
        self.window_height = window_height
        self.switch_window = None

        self.game_timer: GameTimer = None

        self.width_indent = (window_width - self.level_width * self.dot_size) // 2
        self.height_indent = (window_height - self.level_height * self.dot_size) // 2

        number_players.set(len(set(filter(lambda dt: 0xF0 <= dt <= 0xF7, flatten(self.level)))))
        self.load_sprites()

    def win(self):
        self.switch_window = True

    def next_window(self):
        if self.switch_window:
            next_wind = StatisticsWindow(window_width=self.window_width, window_height=self.window_height,
                                         dot_size=64, lvl=self.path,
                                         time=f'{self.game_timer.get_time().total_seconds():.2f}s')
            self.kill_sprites()
            return next_wind
        return self

    def load_sprites(self):
        for priority in range(4):
            for y, line in enumerate(self.level):
                for x, dot in enumerate(line):
                    match dot:
                        case 0x01 if priority == 1:
                            self.sprites.append(
                                Wall(self.width_indent + self.dot_size * x, self.height_indent + self.dot_size * y,
                                     size=self.dot_size))
                        case _ if 0x10 <= dot <= 0x1F and priority == 3:
                            self.sprites.append(
                                Button(self.width_indent + self.dot_size * 0.50 // 2 + self.dot_size * x,
                                       self.height_indent + self.dot_size * 0.50 // 2 + self.dot_size * y,
                                       size=int(self.dot_size * 0.50), button_id=dot - 0x10))
                        case _ if 0x20 <= dot <= 0x2F and priority == 0:
                            self.sprites.append(
                                Gate(self.width_indent + self.dot_size * x,
                                     self.height_indent + self.dot_size * y,
                                     size=int(self.dot_size), gate_id=dot - 0x20, type_or=True))
                        case _ if 0x30 <= dot <= 0x3F and priority == 0:
                            self.sprites.append(
                                Gate(self.width_indent + self.dot_size * x,
                                     self.height_indent + self.dot_size * y,
                                     size=int(self.dot_size), gate_id=dot - 0x30, type_or=False))
                        case _ if 0xF0 <= dot <= 0xF7 and priority == 2:
                            self.sprites.append(
                                Player(self.width_indent + self.dot_size * 0.25 // 2 + self.dot_size * x,
                                       self.height_indent + self.dot_size * 0.25 // 2 + self.dot_size * y,
                                       size=int(self.dot_size * 0.75), player_id=dot - 0xF0,
                                       base_speed=self.dot_size // 10))
                        case 0x03 if priority == 0:
                            self.sprites.append(
                                Win(self.width_indent - self.dot_size * 0.25 // 2 + self.dot_size * x,
                                    self.height_indent - self.dot_size * 0.25 // 2 + self.dot_size * y,
                                    size=int(self.dot_size * 1.25), win_callbacks=(self.win,)))

        self.sprites.append(CurrentPlayer(self.dot_size // 2, self.dot_size // 2, self.dot_size))
        self.game_timer = GameTimer(self.dot_size // 2, self.window_height - self.dot_size * 1.5, self.dot_size)

    def __del__(self):
        self.kill_sprites()

    def kill_sprites(self):
        for sprite in self.sprites:
            sprite.kill()
        self.game_timer.kill()

    def restart(self):
        self.kill_sprites()
        self.load_sprites()
