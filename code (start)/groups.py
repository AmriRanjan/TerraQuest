from settings import *
from support import import_image # to utilise this reusable component and get surfaces of files efficiently
from character import Entity

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()  # no group parameter as this class extends pygame.sprite.Group, which manages sprites rather than being added to a group itself
        self.display_surface = pygame.display.get_surface()
        self.offset = vector() # offset represents the camera movement by shifting the surrounding elements of the player, initially set to (0,0)
        self.shadow_image = import_image("graphics/other/shadow")

    def draw(self, player_center):
        # negative offset values as we want to move the surrounding world elements in the opposite direction to the player movement to give illusion of a camera
        self.offset.x = -(player_center[0] - WINDOW_WIDTH / 2) 
        self.offset.y = -(player_center[1] - WINDOW_HEIGHT / 2)

        bg_sprites = [sprite for sprite in self if sprite.z < WORLD_LAYERS['main']]
        # rearrange sprites in 'main' layer ascending by y-val
        main_sprites = sorted([sprite for sprite in self if sprite.z == WORLD_LAYERS['main']], key = lambda sprite: sprite.y_sort)
        fg_sprites = [sprite for sprite in self if sprite.z > WORLD_LAYERS['main']]

        for layer in (bg_sprites, main_sprites, fg_sprites):
            for sprite in layer: # iterate through all sprites in the group as self is a pygame.sprite.Group
                if isinstance(sprite, Entity):
                    self.display_surface.blit(self.shadow_image, sprite.rect.topleft + self.offset + vector(40,110)) # position shadow below feet
                self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset) 
                # blit each sprite's image at its rect's top-left position adjusted by the offset every frame to create camera movement effect

class MatchSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()  # no group parameter as this class extends pygame.sprite.Group, which manages sprites rather than being added to a group itself
        self.display_surface = pygame.display.get_surface()

    def draw(self):
        for sprite in sorted(self, key = lambda sprite: sprite.z): 
            # iterate through all sprites in the group as self is a pygame.sprite.Group and sort them by their z attribute via a lambda function
            self.display_surface.blit(sprite.image, sprite.rect) 
        