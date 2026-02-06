from settings import *
from timer import Timer

class DialogTree:
    def __init__(self, character, player, all_sprites, font, del_dialog):
        self.del_dialog = del_dialog
        self.character = character
        self.player = player
        self.font = font
        self.all_sprites = all_sprites
        
        self.dialog = character.get_dialog() # dialog text in an array for the current character
        self.dialog_num = len(self.dialog) # hold length of dialog array
        self.dialog_index = 0 # index to search which message in the array is wanted

        self.current_dialog = DialogSprite(self.dialog[self.dialog_index], self.character, self.all_sprites, self.font)
        self.dialog_timer = Timer(500, autostart = True)
        self.character.in_dialog = True
    
    def input(self):
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_SPACE] and self.dialog_timer.active == False:
            self.current_dialog.kill() # delete contents of self.current_dialog, so delete DialogSprite object
            self.dialog_index += 1
            if self.dialog_index < self.dialog_num: # if another dialog message left in the list
                self.current_dialog = DialogSprite(self.dialog[self.dialog_index], self.character, self.all_sprites, self.font)
                self.dialog_timer.start()
            else:
                self.del_dialog(self.character) # end dialog by in main.py by setting self.dialog_tree flag to False, and unblocking player movement
            
    def update(self):
        self.dialog_timer.update()
        self.input()

class DialogSprite(pygame.sprite.Sprite):
    def __init__(self, message, character, groups, font):
        super().__init__(groups)
        self.z = WORLD_LAYERS['top']

        # not attributes, as store as local variables that can change
        text_surf = font.render(message, False, COLORS['black'])
        padding = 10 # to give a distance between ends of textbox
        width = max(30, text_surf.get_width() + padding * 2) # minimum width of textbox is 30px, to prevent very small textboxes if the text is small
        height = text_surf.get_height() + padding * 2

        surf = pygame.Surface((width,height))
        surf.fill(COLORS['pure white']) # white box surface
        surf.blit(text_surf, text_surf.get_frect(center = (width / 2, height / 2))) # blitting text on the box to form a textbox
        self.image = surf
        self.rect = self.image.get_frect(midbottom = character.rect.midtop + vector(0,-10)) 
        # position textbox slightly above the middle of the character (10px) so you can instinctively tell who is talking 

    