from settings import *
from timer import Timer
from random import choice
from monster import Monster

# creating sprite which consists of position rectangle and graphic surface by inheriting from the parent class pygame.sprite.Sprite
class Entity(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, facing_direction):
        super().__init__(groups)
        # initialise parent class by calling its constructor first so we can use its functionality of sprite groups, drawing and updates
        self.z = WORLD_LAYERS['main'] # hard set to this value as all entities must remain in this layer always

        # graphics
        self.frame_index = 0
        self.frames = frames
        self.facing_direction = facing_direction

        # movement
        self.direction = vector() # create a vector to store movement direction
        self.blocked = False

        # sprite setup
        # self.image = self.frames[direction type/state][self.frame_index]
        self.image = self.frames[self.get_state()][self.frame_index]
        self.rect = self.image.get_frect(center = pos) # used floating point rectangle for more precise positions
        
        # halve the width and decrease 60px from height of entity rectangle
        self.hitbox = self.rect.inflate(-self.rect.width/2, -60)

        self.y_sort = self.rect.centery

    def animate(self, dt):
        # increment frame index based on animation speed constant set in settings.py, and time passed, so independent of framerate
        self.frame_index += ANIMATION_SPEED * dt

        self.image = self.frames[self.get_state()][int(self.frame_index % len(self.frames[self.get_state()]))]
        # apply modulus so that if frame_index increases to more than index of last image, 
        # then mod it to get the remainder and assign this to act as frame index, making sure 
        # the frame index for the list frames never gives error 

    def get_state(self):
        # only update state if player is moving, so moving = either True or False depending on if self.direction vector is empty or not
        moving = bool(self.direction)
        if moving:
            if self.direction.x != 0:
                self.facing_direction = 'right' if self.direction.x > 0 else 'left'
            if self.direction.y != 0:
                self.facing_direction = 'down' if self.direction.y > 0 else 'up' 
        return f'{self.facing_direction}{'' if moving else '_idle'}' # if it is idle, then return the direction object faces, but idle version
 
    def block(self):
        self.blocked = True
        self.direction = vector(0,0) # no movement

    def unblock(self):
        self.blocked = False

    def change_direction(self, target_pos):
        relation = vector(target_pos) - vector(self.rect.center) # vector from the Entity object, to the target position coordinates
        if abs(relation.y) < 30: # same horizontal plane, with 30px leeway both sides
            self.facing_direction = 'right' if relation.x > 0 else 'left'
        if abs(relation.x) < 30: # same vertical plane, with 30px leeway both sides
            self.facing_direction = 'down' if relation.y > 0 else 'up'

# creating sprite which consists of position rectangle and graphic surface by inheriting from the parent class Entity
class NPC(Entity):
    def __init__(self, pos, frames, groups, facing_direction, trainer_data, nurse): # satisfy parameters of parent class Sprite
        super().__init__(pos, frames, groups, facing_direction) # initialising parent constructor
        self.trainer_data = trainer_data
        self.timers = {
            'look_around' : Timer(1500, autostart = True, repeat = True, func = self.random_viewing_direction)
            }
        self.nurse = nurse
        self.trainer_monsters = {index: Monster(name, level) for index, (name, level) in trainer_data['monsters'].items()} if 'monsters' in trainer_data else None
        # list comprehension to store the monsters for each NPC, excluding the nurse which has no monsters stored under its nested dictionary in game_data.py
        
        self.viewing_directions = trainer_data['directions']
        self.in_dialog = False

    def random_viewing_direction(self):
        self.facing_direction = choice(self.viewing_directions)
    
    def get_dialog(self):
        return self.trainer_data['dialog'][f'{'defeated' if self.trainer_data['defeated'] else 'default'}']
        # f-string used to select which type of dialog wanted depending on the value of the defeated key-value pair in self.trainer_data

    def update(self, dt):
        if not self.in_dialog:
            for timer in self.timers.values(): # iterate through every timer and run their respective update method
                timer.update()
        self.animate(dt)

# creating sprite which consists of position rectangle and graphic surface by inheriting from the parent class Entity
class Player(Entity):
    def __init__(self, pos, frames, groups, facing_direction, collision_sprites): # satisfy parameters of parent class Sprite
        super().__init__(pos, frames, groups, facing_direction) # initialising parent constructor
        self.collision_sprites = collision_sprites

    def input(self):
        keys = pygame.key.get_pressed() # get the current state of all keyboard keys
        key_vector = vector() # gives blank vector with x and y as 0

        if keys[pygame.K_UP]: # check if up arrow key is pressed
            key_vector.y = -1 # set y component of vector to -1 to indicate upward movement
        if keys[pygame.K_DOWN]: # check if down arrow key is pressed
            key_vector.y = 1 # set y component of vector to 1 to indicate downward movement
        if keys[pygame.K_LEFT]: # check if left arrow key is pressed
            key_vector.x = -1 # set x component of vector to -1 to indicate leftward movement
        if keys[pygame.K_RIGHT]: # check if right arrow key is pressed
            key_vector.x = 1 # set x component of vector to 1 to indicate rightward movement

        self.direction = key_vector.normalize() if key_vector else key_vector 
        # update the player's direction vector based on input and normalise it, as long as key_vector present

    def move(self, dt):
        self.rect.centerx += self.direction.x * 300 * dt # move the player based on direction, speed (250 pixels per second), and delta time for frame rate independence
        self.hitbox.centerx = self.rect.centerx # update x hitbox position to be aligned centrally with entity rectangle
        self.collisions('horizontal')

        self.rect.centery += self.direction.y * 300 * dt # move the player based on direction, speed (250 pixels per second), and delta time for frame rate independence
        self.hitbox.centery = self.rect.centery # update y hitbox position to be aligned centrally with entity rectangle
        self.collisions('vertical')

    def collisions(self, axis):
        for sprite in self.collision_sprites:
            if sprite.hitbox.colliderect(self.hitbox): # check if hitbox rectangle of sprite is in contact with hitbox rectangle of player
                if axis == 'horizontal':    
                    # prevent player hitbox and hence rectangle moving any further in the direction of obstacle
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0:
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx # update x hitbox position to be aligned centrally with entity rectangle
                else:    
                    # prevent player hitbox and hence rectangle moving any further in the direction of obstacle
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top 
                    if self.direction.y < 0:
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery # update y hitbox position to be aligned centrally with entity rectangle

    # update method called every frame to update the sprite's methods
    def update(self, dt):
        self.y_sort = self.rect.centery
        if not self.blocked:
            self.move(dt)
            self.input()
        self.animate(dt)

