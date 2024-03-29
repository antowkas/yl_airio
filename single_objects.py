from pygame.sprite import Group
from pg_utilities import Mutable

all_sprites = Group()
wall_sprites = Group()
button_sprites = Group()
gate_sprites = Group()
player_sprites = Group()
win_sprites = Group()

active_player_id = Mutable(0)
number_players = Mutable(1)
