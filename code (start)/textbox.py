import pygame
from settings import *

class Textbox():
    def __init__(self, display_surface, x, y, fonts, input_type):
        self.textbox_rect = pygame.Rect(x,y, 350, 60) # approximate height and width defined at the position given
        self.text = "" # initially no text shown
        self.fonts = fonts
        self.display_surface = display_surface
        self.active = False # fixed attribute indicating if the box should be able to take text or not
        self.input_type = input_type
        if self.input_type == 'username':
            self.checking_message = "USERNAME VALID"
        else:
            self.checking_message = "PASSWORD VALID"

        self.message_color = (255, 0, 0) # start screen with invalid username as no entry yet, so red hue

        self.cross_img = pygame.transform.scale(pygame.image.load("graphics/ui/red_cross.png").convert_alpha(), (23, 23))
        self.tick_img = pygame.transform.scale(pygame.image.load("graphics/ui/green_tick.png").convert_alpha(), (23, 23))

        self.max_width = 350

    def display(self):
        self.text_surf = self.fonts['credentials'].render(self.text, False, COLORS['black']) # any text surface that is blitted
        pygame.draw.rect(self.display_surface, COLORS['white'], self.textbox_rect, 0)
        self.display_surface.blit(self.text_surf, (self.textbox_rect.x + 7, self.textbox_rect.y + 5)) # padding added from left and top edges of textbox

        if self.input_type == 'username':
            valid = self.is_valid_username() # if the object is a username, then validate using its is_valid_username() method
        else:
            valid = self.is_valid_password() # if the object is a pass, then validate using its is_valid_password() method
        
        if valid:
            self.message_color = (0, 255, 0) # bright green colour for the message text of this textbox
            icons = self.tick_img # and a green tick icon being blitted instead of the usual red cross
        else:
            self.message_color = (255, 0, 0) # if not valid, then bright red colour for the message text of this textbox
            icons = self.cross_img # and a red cross icon being blitted

        message_surf = self.fonts['bold'].render(self.checking_message, False, self.message_color)
        message_rect = message_surf.get_rect(topleft = (self.textbox_rect.x, self.textbox_rect.y + self.textbox_rect.height + 5)) 
        # message is 5px below the bottom of textbox
        self.display_surface.blit(message_surf, message_rect)
        self.display_surface.blit(icons, (message_rect.right + 5, message_rect.y)) # and the icon is 5px on the right of the message for padding
    
    def check_input(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # left click as event.button == 1
                self.active = self.textbox_rect.collidepoint(event.pos) # if cursor collides with textbox, then self.active is True, else it stays False
            if self.active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1] # delete last character for each backspace pressed
                else:
                    new_text = self.text + event.unicode
                    new_surf = self.fonts['credentials'].render(new_text, False, COLORS['black'])
                    if new_surf.get_width() <= self.max_width:
                        self.text = new_text # other than that, whatever they enter must be characters for their credentials

    def is_alphanumeric(self):
        for char in self.text:
            if char.isalnum(): 
                # check if the character is a letter or number using python's function that checks if characters are alphanumeric only
                return True
        return False

    def is_valid_length(self): # check if the textbox that calls this is of the right length
        if self.input_type == 'username':
            return 3 <= len(self.text) <= 10
        else:
            return 12 <= len(self.text) <= 15

    def special_char(self): # verify if a special character in the text has been inputted
        special_chars = "!\@#$%^&*()-_=+[]{};:,.<>/?|"
        for each_char in self.text:
            if each_char in special_chars:
                return True # as soon as there is 1 special character, then the function stops and returns True, no more checks as then the flag can become False
        return False
    # only if every character has been passed and we still haven't returned out the loop yet, then True must've not been outputted 
    # and thus there is no special characters here, so return False
        
    def is_valid_username(self):
        return self.is_alphanumeric() and self.is_valid_length() # requirements for username
    
    def is_valid_password(self):
        return self.is_valid_length() and self.special_char() and self.is_alphanumeric() # requirements for password

    def update(self):
        self.display()