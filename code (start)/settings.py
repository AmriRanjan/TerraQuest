# import necessary modules and exit function

import pygame
from pygame.math import Vector2 as vector 
from sys import exit

# settings constants for overworld

WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 650
TILE_SIZE = 64 
ANIMATION_SPEED = 6
BATTLE_OUTLINE_WIDTH = 4

# initialising colours, layers, and positions for game

COLORS = {
	'white': '#f4fefa', 
	'pure white': '#ffffff',
	'dark': '#2b292c',
	'light': '#c8c8c8',
	'gray': '#3a373b',
	'gold': '#ffd700',
	'light-gray': '#4b484d',
	'fire':'#f8a060',
	'water':'#50b0d8',
	'plant': '#64a990', 
	'black': '#000000', 
	'red': '#f03131',
	'blue': '#66d7ee',
    'normal': '#ffffff'
}

WORLD_LAYERS = {
	'water': 0,
	'bg': 1,
	'shadow': 2,
	'main': 3,
	'top': 4
}

BATTLE_POSITIONS = {
	'left': {'top': (360, 260), 'center': (190, 400), 'bottom': (410, 520)},
	'right': {'top': (900, 260), 'center': (1110, 350), 'bottom': (900, 520)}
}

BATTLE_LAYERS =  {
	'outline': 0,
	'name': 1,
	'monster': 2,
	'effects': 3,
	'overlay': 4
}

# settings for battle choices menu

BATTLE_CHOICES = {
	'full': {
		'fight':  {'pos' : vector(30, -40), 'icon': 'sword'},
		'defend': {'pos' : vector(40, 0), 'icon': 'shield'},
		'catch':  {'pos' : vector(30, 40), 'icon': 'hand'}},
	
	'limited': {
		'fight':  {'pos' : vector(30, -40), 'icon': 'sword'},
		'defend': {'pos' : vector(40, 0), 'icon': 'shield'}}
}