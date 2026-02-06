from settings import *
from support import draw_stats_bars
from timer import Timer

# creating sprite which consists of position rectangle and graphic surface by inheriting from the parent class pygame.sprite.Sprite
class Sprite(pygame.sprite.Sprite): 
    def __init__(self, pos, image, groups, z = WORLD_LAYERS['main']):
        # initialise parent class by calling its constructor first so we can use its functionality of sprite groups
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_frect(topleft = pos) # used floating point rectangle for more precise positions
        self.z = z # as can change layers it is in when needed
        self.y_sort = self.rect.centery
        self.hitbox = self.rect.copy()

class BorderSprite(Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(pos, image, groups)
        self.hitbox = self.rect.copy()

class CollidableSprite(Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(pos, image, groups)
        self.hitbox = self.rect.inflate(0, -self.rect.height * 0.4) # smaller height hitbox than its rectangle

class MonsterGrassSprite(Sprite):
    def __init__(self, pos, image, groups, biome, monsters, level):
        self.biome = biome
        # sand must have a lower layer to be drawn beneath the player and 'main' objects in AllSprite's draw method, at all times
        super().__init__(pos, image, groups, WORLD_LAYERS['main' if biome != 'sand' else 'bg'])
        self.y_sort -= 40
        # effectively gives ice and forest grass tiles lower y_sort so when player walks down it, there is a less distance travelled 
        # until player's y-val is higher and so is ordered and printed above in main_sprites
        
        self.monsters = monsters.split(',')
        self.level = level

class AnimatedSprite(Sprite): # child class that inherits features, methods and attributes from Sprite class

    def __init__(self, pos, frames, groups, z = WORLD_LAYERS['main']): # satisfy parameters of parent class Sprite

        self.frame_index = 0
        self.frames = frames
        super().__init__(pos, frames[self.frame_index], groups, z) # passing current frame for drawing

    def animate(self, dt):
        # increment frame index based on animation speed constant set in settings.py, and time passed, so independent of framerate
        self.frame_index += ANIMATION_SPEED * dt

        # selecting frame to show from list of frames
        self.image = self.frames[int(self.frame_index) % len(self.frames)]
        # apply modulus so that if frame_index increases to more than index of last image, 
        # then mod it to get the remainder and assign this to act as frame index, making sure 
        # the frame index for the list frames never gives error 

    def update(self, dt):
        self.animate(dt)

class TransitionSprite(Sprite):
    def __init__(self, pos, size, target, groups):
        image = pygame.Surface(size) # no colour specified as its image is supposed to be unnoticeable
        super().__init__(pos, image, groups)
        self.target = target

class MonsterSprite(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, monster, index, pos_index, entity, apply_move):
        # assigning attributes
        super().__init__(groups) # take advantage of the groups functionality from pygame.sprite.Sprite parent class
        self.frames = frames
        self.monster = monster
        self.index = index
        self.pos_index = pos_index
        self.entity = entity
        self.z = BATTLE_LAYERS['monster']  # all monsters in match layer should be in the monster layer
        self.target_sprite = None
        self.current_move = None
        self.apply_move = apply_move

        # start at the first frame when animating the monsters in the match screen
        self.frame_index = 0
        self.state = 'idle' # perform idle animations first

        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(center = pos) # position the monster at the centre of the position given
        # position isn't a required attribute as the rect fully defines the sprite’s location, so we save memory

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.state == 'attack' and self.frame_index >= len(self.frames[self.state]): # if attack animation has finished
            self.apply_move(self.target_sprite, self.current_move, self.monster.get_base_damage(self.current_move)) 
            # call the apply_move function passed in from Match class
            self.state = 'idle'

        self.image = self.frames[self.state][int(self.frame_index) % len(self.frames[self.state])]

    def activate_move(self, target_sprite, move):
        self.state = 'attack'
        self.frame_index = 0
        self.target_sprite = target_sprite
        self.current_move = move
        self.monster.reduce_energy(move) # reduce the monster's energy based on the move's cost

    def update(self, dt):
        self.animate(dt)
        self.monster.update(dt) # update the monster's readiness every frame

class MonsterNameSprite(pygame.sprite.Sprite):
    def __init__(self, pos, monster_sprite, groups, font, target = False):
        super().__init__(groups) # take advantage of the groups functionality from pygame.sprite.Sprite parent class
        self.z = BATTLE_LAYERS['name'] # all name sprites in match layer should be in the name layer
        self.monster_sprite = monster_sprite

        name_surf = font.render(monster_sprite.monster.name, False, COLORS['black']) # text of the MonsterSprite that instantiated this class
        padding = 10

        self.image = pygame.Surface((name_surf.get_width() + 2 * padding, name_surf.get_height() + 2 * padding)) # background of each name textbox
        self.image.fill(COLORS['white']) if target == False else self.image.fill(COLORS['light-gray']) # white background for readability????????????????????????????
        self.rect = self.image.get_frect(midtop = pos) # position the background textbox so its midtop point is at the position argument given
        self.image.blit(name_surf, (padding, padding)) # blit the name surface on top of the background textbox

    def update(self, dt):
        if not self.monster_sprite.groups(): # if the respective monster sprite has been removed from all groups (fainted)
            self.kill() # remove the name sprite from all groups as well

class MonsterStatsSprite(pygame.sprite.Sprite):
    def __init__(self, pos, monster_sprite, size, groups, font):
        super().__init__(groups) # take advantage of the groups functionality from pygame.sprite.Sprite parent class
        self.monster_sprite = monster_sprite
        self.image = pygame.Surface(size) # image attribute of sprite
        self.rect = self.image.get_frect(midbottom = pos) # rect attribute of sprite
        self.font = font
        self.z = BATTLE_LAYERS['overlay'] # all stats sprites in match layer should be in the overlay layer
        self.monster_sprite = monster_sprite

    def update(self, dt):
        # placed bar logic here so that the stats update every frame
        self.image.fill(COLORS['white']) # clear previous stat display

        for index, (value, max_value) in enumerate(self.monster_sprite.monster.get_info()):
            color = (COLORS['red'], COLORS['blue'], COLORS['black'])[index] # colours for health, energy and readiness respectively
            if index < 2: # health and energy bars
                text_surf = self.font.render(f'{int(value)}/{int(max_value)}', False, COLORS['black']) # text showing the fraction of current to maximum value for this metric
                text_rect = text_surf.get_frect(topleft = (self.rect.width * 0.05, index * self.rect.height / 2))
                bar_rect = pygame.FRect(text_rect.bottomleft + vector(0, -2), (self.rect.width, 4)) # pos and size arguments

                self.image.blit(text_surf, text_rect)
                draw_stats_bars(self.image, bar_rect, value, max_value, color, COLORS['black'])
            else: # readiness bar
                readiness_rect = pygame.FRect((0, self.rect.height - 2), (self.rect.width, 4)) # pos and size arguments
                draw_stats_bars(self.image, readiness_rect, value, max_value, color, COLORS['white'])

        if not self.monster_sprite.groups(): # if the respective monster sprite has been removed from all groups (fainted)
            self.kill() # remove the stats sprite from all groups as well

class MoveSprite(AnimatedSprite):

    def __init__(self, pos, frames, groups):
        super().__init__(pos, frames, groups, BATTLE_LAYERS['overlay']) # moves' visuals should be in overlay layer
        self.rect.center = pos

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index >= len(self.frames):
            self.kill() # remove the move sprite from all groups once its animation has finished via its last frame's index being incremented over
        else:
            self.image = self.frames[int(self.frame_index)] # no need for modulus as we are already checking if we are inside the length of frames list
        
    def update(self, dt):
        self.animate(dt)

class CrossSprite(Sprite):
    def __init__(self, pos, frames, groups, duration):
        super().__init__(pos, frames, groups, z = BATTLE_LAYERS['overlay']) # cross visuals should be in overlay layer and initialising parent Sprite class
        self.rect.center = pos
        self.kill_timer = Timer(duration, autostart = True, func = self.kill) # timer to remove the cross sprite after duration milliseconds

    def update(self, dt):
        self.kill_timer.update() # update the timer every frame by calling its update method which checks when it stops and calls its function