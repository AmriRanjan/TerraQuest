# these are required for loading assets and TMX maps in a modular and maintainable way
from settings import *
from os.path import join
from os import walk
from pytmx.util_pygame import load_pygame

# import functions to import data quickly
def import_image(*path, alpha = True, format = 'png'): # imports a single png image
	full_path = join(*path) + f'.{format}' # creates a path for the file using join method, which allows path to work for all operating systems
	# produces and returns the image
	surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert() 
	return surf

def import_folder(*path):
    # list to store all loaded image surfaces (animation frames)
    frames = []

    # walk through the directory created from the given path to retrieve folders, subfolders, and image names
    for folder_path, sub_folders, image_names in walk(join(*path)):
        
        # sorting image filenames by number as int(name.split('.')[0]) used. The name.split('.')[0] operation extracts the number before ".png"
        for image_name in sorted(image_names, key=lambda name: int(name.split('.')[0])):
            
            # creates full file path to the image
            full_path = join(folder_path, image_name)
            
            # load the image as a pygame Surface
            surf = pygame.image.load(full_path).convert_alpha()
            
            # append the loaded image surface to frames list
            frames.append(surf)

    # return all images in frames for animations
    return frames

# same as import_folder, but also stores image's file name in a dictionary, so it can be searched with the name easily
def import_folder_dict(*path):
	frames = {}
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image_name in image_names:
			full_path = join(folder_path, image_name)
			surf = pygame.image.load(full_path).convert_alpha()
			frames[image_name.split('.')[0]] = surf
	return frames

# goes through a folder that has several subfolders, and imports all the images in each subfolder
def import_sub_folders(*path):
	# dictionary holds key - subfolder name, and value - list of surfaces/images
	frames = {}
	
    # walk through the directory as __ represents current folder path, access the subfolders, and __ represents files in the folder
	for _, sub_folders, __ in walk(join(*path)):
		# if sub_folders exist
		if sub_folders:
			for sub_folder in sub_folders:
				# all images in this subfolder and them in dictionary with subfolder name as the key
				frames[sub_folder] = import_folder(*path, sub_folder)
	# return dictionary
	return frames

def import_tilemap(cols, rows, *path):
	# dictionary to store tiles where key is position in tilemap, and value is surface/image of tile
	frames = {}
	# loads entire tileset as single surface
	surf = import_image(*path)
	# height and width of tile
	cell_width, cell_height = surf.get_width() / cols, surf.get_height() / rows
	for col in range(cols):
		for row in range(rows):

			# creating a new rectangular surface for each tile

			# creating rectangular surface for tile
			cutout_rect = pygame.Rect(col * cell_width, row * cell_height,cell_width,cell_height)
			cutout_surf = pygame.Surface((cell_width, cell_height))
			cutout_surf.fill('green')
			cutout_surf.set_colorkey('green')

			# displaying tile from tileset onto new surface
			cutout_surf.blit(surf, (0,0), cutout_rect)
			# store the tile surface in dictionary using its grid position as key
			frames[(col, row)] = cutout_surf
	return frames

def character_import(cols, rows, *path):
	frame_dict = import_tilemap(cols,rows,*path) # dictionary of each tile image in tileset
	new_dict = {} # dictionary holding direction types, and tile images for them, currently empty

	# adding frame images for each direction type in new_dict
	for row, direction in enumerate(('down', 'left', 'right', 'up')):
		new_dict[direction] = [frame_dict[(col, row)] for col in range(cols)]
		# first column of each row is idle animation image, so used f-string to make another entry in dictionary for the idle version of this same direction
		new_dict[f'{direction}_idle'] = [frame_dict[(0,row)]]
	return new_dict

def all_characters_import(*path):
	new_dict = {}
	# walk through the directory as __ represents current folder path (and __ indicates to pygame that it's not wanted),
	# __ represents the subfolders (and __ indicates to pygame that it's not wanted),
	# and image_names represents file names in the folder
	for __, __, image_names in walk(join(*path)):
		for image in image_names:
			image_name = image.split('.')[0]
			# For each character found, the character_import subroutine is then called to populate its associated value with all the directions and direction frame images
			new_dict[image_name] = character_import(4,4, *path, image_name)
	return new_dict

def coast_import(cols, rows, *path):
	frame_dict = import_tilemap(cols, rows, *path) # dictionary of each tile image in tileset
	new_dict = {} # dictionary holding terrain types, side types, and tile images for them, currently empty
	terrains = ['grass', 'grass_i', 'sand_i', 'sand', 'rock', 'rock_i', 'ice', 'ice_i']
	# all the side types along with their coordinates for each 3x3 tile grid in the tileset
	sides = {
		'topleft': (0,0), 'top' : (1,0), 'topright': (2,0),
		'left': (0,1), 'right': (2,1), 'bottomleft': (0,2),
		'bottom': (1,2), 'bottomright': (2,2)
	}
	
	# looping through each terrain and making it a key in new_dict
	for index, terrain in enumerate(terrains):
		new_dict[terrain] = {}
		for sidetype, pos in sides.items():
			# adding frame images for each terrain type and side type in new_dict

			# pos[0] + index * 3 to select the correct column within the 3×3 tile group and shift it by a multiple of 3
			# for each terrain column in the tileset as we go through the for loop
			new_dict[terrain][sidetype] = [frame_dict[(pos[0] + index * 3, pos[1] + row)] for row in range(0, rows, 3)]
			# looping over rows in increments of 3 as each tile group or frame is 3 tiles tall using list comprehension
	return new_dict

def tmx_import(*path):
	tmx_dict = {} # dictionary for all the tilemaps that main.py will access from
	for folder_path, sub_folders, file_names in walk(join(*path)): # go down the path supplied until each file name retrieved from the folder
		for file in file_names:
			# for each tilemap file, create a key of its name (first half by excluding everything after . and taking 0 index), and link to 
			# its full file path for easy fetching
			key = file.split('.')[0]
			tmx_dict[key] = load_pygame(join(folder_path, file))
	return tmx_dict

def monster_import(cols, rows, *path):
	monster_dict = {}
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image in image_names:
			image_name = image.split('.')[0]
			monster_dict[image_name] = {} # new entry for each monster where the key is its name
			frame_dict = import_tilemap(cols, rows, *path, image_name) # temporary dictionary to hold current monster's frames 
			for row, key in enumerate(('idle', 'attack')):
				monster_dict[image_name][key] = [frame_dict[(col,row)] for col in range(cols)]
				# each monster name now has two key-value pairs inside it, one with the key 'idle' and one with the key 'attack'
				# these keys are respectively associated to a list with all the frame images from frame_dict from the first (idle) row or second (attack) row of tilemap
	return monster_dict 

# game functions

def draw_stats_bars(surface, rect, value, max_value, color, bg_color):
	ratio = rect.width/max_value # ratio for how many pixels wide one unit of the stat value should be
	bg_rect = rect.copy() # same rectangle for background of bar as the main bar itself
	progress = max(0, min(rect.width, value * ratio)) # with of filled bar cannot be negative, and cannot be larger than width of the whole bar
	progress_rect = pygame.FRect(rect.topleft, ((progress), rect.height)) # rectangle with a current width relating to the stat it possesses
	pygame.draw.rect(surface, bg_color, bg_rect, 0)
	pygame.draw.rect(surface, color, progress_rect, 0)

def check_connection(radius, entity, target):
	tolerance = 30
	relation = vector(target.rect.center) - vector(entity.rect.center) # vector going from entity, or our player, to the target, or NPC
	if relation.length() < radius: # if entity or player is in the defined area around target
		if entity.facing_direction == 'left' and relation.x < 0 and abs(relation.y) < tolerance or\
		entity.facing_direction == 'right' and relation.x > 0 and abs(relation.y) < tolerance or\
		entity.facing_direction == 'up' and relation.y < 0 and abs(relation.x) < tolerance or\
		entity.facing_direction == 'down' and relation.y > 0 and abs(relation.x) < tolerance:
			return True

def attack_importer(*path): # imports all attack animations from a folder into a dictionary
	attack_dict = {}
	for folder_path, sub_folders, image_names in walk(join(*path)):
		for image in image_names:
			image_name = image.split('.')[0]
			attack_dict[image_name] = list(import_tilemap(4, 1, folder_path, image_name).values()) # each attack animation has 4 columns and 1 row in its tilemap
	return attack_dict