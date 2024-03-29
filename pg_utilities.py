from math import sqrt
from typing import Tuple

from pygame.image import load as img_load
from pygame import Color
from os.path import join, isfile
from sys import exit as sys_exit


def load_image(name, colorkey=None):
    fullname = join('data', name)
    if not isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys_exit()
    image = img_load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def read_bin_level_data(path):
    with open(path, 'rb') as file:
        lvl_width = int.from_bytes(file.read(1))
        lvl_height = int.from_bytes(file.read(1))
        return tuple(tuple(
            int.from_bytes(file.read(1)) for _ in range(lvl_width)
        ) for _ in range(lvl_height))


def player_color(color_code: int):
    return byte_color(color_code, 360, 80, 100, 85)


def button_color(color_code: int, active=False):
    return hex_color(color_code, 360, (60, 80)[active], 100, 85)


def byte_color(color_code: int, h=360, s=360, v=100, a=100):
    return rough_hsva_color(color_code, 8, h, s, v, a)


def hex_color(color_code: int, h=360, s=360, v=100, a=10):
    return rough_hsva_color(color_code, 16, h, s, v, a)


def rough_hsva_color(color_code, rough=361, h=360, s=100, v=100, a=100):
    if not (0 <= color_code < rough):
        raise ValueError
    color = Color(255, 255, 255)
    color.hsva = (int(h / rough * color_code), s, v, a)
    return color


def normalize_vector(vector):
    length = sqrt(vector[0] ** 2 + vector[1] ** 2)
    if length != 0:
        return vector[0] / length, vector[1] / length
    else:
        return 0., 0.


class Mutable:
    def __init__(self, value):
        self.value = value

    def set(self, new_value):
        self.value = new_value

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.value)


def flatten(matrix: list[list[int]]) -> Tuple[int]:
    h = len(matrix)
    w = len(matrix[0])
    return tuple(matrix[i][j] for i in range(h) for j in range(w))


def read_txt_level_data(path):
    with open(path, 'r', encoding="UTF-8") as file:
        data = file.readlines()
    return tuple(tuple(map(lambda x: int(x, 16), line.rstrip().split(", "))) for line in data)


def write_level_in_bin(level_data, path):
    width, height = len(level_data[0]), len(level_data)
    with open(path, "wb") as file:
        file.write(bytes((width, height, *flatten(level_data))))


if __name__ == '__main__':
    lvl = read_txt_level_data("data/levels/level4.txt")
    write_level_in_bin(lvl, "data/levels/level4.bin")
