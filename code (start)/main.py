import sys
from settings import *
from game_data import *
from button import Button
from pytmx.util_pygame import load_pygame # import pytmx module to render tmx maps

from sprite import Sprite, AnimatedSprite, MonsterGrassSprite, BorderSprite, CollidableSprite, TransitionSprite
from character import Player, NPC
from groups import AllSprites
from dialog import DialogTree
from monster import Monster
from index import MonsterIndex
from match import Match
from timer import Timer
from textbox import Textbox
from database import Database

from support import *

class Game:
     
    def __init__(self):
        pygame.init()

        self.db = Database() # creates database tables
        self.userid = None

        # setting up screen and display using settings.py constants
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TerraQuest")

        # setting up clock for framerate control on different devices so game runs at same speed
        self.clock = pygame.time.Clock()
        self.encounter_timer = Timer(2000, func = self.monster_encounter)

        # setting up background image and title
        self.bg = pygame.transform.scale(pygame.image.load("graphics/backgrounds/main_menu_bg.jpg").convert_alpha(), (WINDOW_WIDTH, WINDOW_HEIGHT))

        self.play_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50), "PLAY", self.get_font(74), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
        self.leaderboard_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50), "LEADERBOARD", self.get_font(55), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
        self.help_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 150), "HELP", self.get_font(74), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)        
        self.quit_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 250), "QUIT", self.get_font(64), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
        # replace rotation attribute with True to make only cog icon spin when hovered over, all other buttons are default set as False
        self.cog_button = Button(pygame.transform.smoothscale(pygame.image.load("graphics/ui/cog.png").convert_alpha(), (50,50)), 
                            (WINDOW_WIDTH - 32, WINDOW_HEIGHT - 32), None, None, None, None, None, 0, True)
        self.script_button = Button(pygame.transform.smoothscale(pygame.image.load("graphics/ui/script.png").convert_alpha(), (65,50)), 
                            (WINDOW_WIDTH - 1168, WINDOW_HEIGHT - 32), None, None, None, None, None, 0)
        self.title = Button(None, 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 5.5), "TERRAQUEST", self.get_font(125), COLORS['white'], COLORS['white'], COLORS['black'], 3)
                             # made hover color for title white so visually, color doesn't change when mouse moves over it
        
        # graphics initialisation
        self.loading_container = pygame.Rect(WINDOW_WIDTH//2 - 600//2, WINDOW_HEIGHT//2 + 50, 600, 50) # draw a rectangle to contain loading bar (boundary box)
        self.loading_width = 0

        self.arrow_keys = pygame.transform.scale(pygame.image.load("graphics/ui/arrow_keys.png").convert_alpha(), (300,150))
        self.mouse = pygame.transform.scale(pygame.image.load("graphics/ui/mouse.png").convert_alpha(), (150,150))
        self.scroll = pygame.transform.scale(pygame.image.load("graphics/ui/scroll.png").convert_alpha(), (1000,800))

        # sprite groups
        self.all_sprites = AllSprites() # group to hold all sprites in the game and update/draw them together
        self.collision_sprites = pygame.sprite.Group()
        self.character_sprites = pygame.sprite.Group() # for easy access to all the enemy trainers
        self.transition_sprites = pygame.sprite.Group() # for easy access to all the transition areas
        self.grass_sprites = pygame.sprite.Group()

        # transition / screen tinting prep
        self.transition_target_properties = None # for easy access to the custom properties of each transition area in TransitionSprite's attributes
        self.tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.tint_mode = 'untint' # only start tinting when this is set to 'tint', as want rest of the game to stay bright
        self.tint_progress = 0 # opacity of dark screen
        self.tint_direction = -1 # use this to decrease tint_progress to decrease opacity and make screen go from dark to light again
        self.tint_speed = 600

        # map initialisation
        self.load_map()
        self.setup(self.tmx_maps['world'], 'house') # setup the map with player starting position at 'house' (can be changed later)

        # settings initialisation
        self.music_on = "ON"
        self.sfx_on = "ON"
        self.battle_animations_on = "HIGH"
        self.midway_settings = False

        # monsters 
        self.player_monsters = { 
            0: Monster('Volcario', 30),
            1: Monster('Glacifox', 29),
            2: Monster('Budlet', 3),
            3: Monster('Vyperion', 24),
            4: Monster('Sparkadillo', 24),
            5: Monster('Beluin', 24),
            6: Monster('Jacana', 2),
            7: Monster('Chuchu', 3)
        }

        # overlays for the game (e.g. monster index) 
        self.dialog_tree = None
        self.monster_index = MonsterIndex(self.player_monsters, self.fonts, self.monster_frames)
        self.monster_index_open = False
        self.match = None

    def get_font(self, size): # helpful function to get font in desired size to decrease code repetition
        return pygame.font.Font("graphics/fonts/PixelifySans-Bold.ttf", size)

    def signup(self):

        # gave input type of 'username' for username checks to occur for this object
        username_textbox = Textbox(self.display_surface, WINDOW_WIDTH//2 - 500, WINDOW_HEIGHT//2 - 40, self.fonts, 'username')
        # gave input type of 'password' for password checks to occur for this object
        password_textbox = Textbox(self.display_surface, WINDOW_WIDTH//2 - 500, WINDOW_HEIGHT//2 + 120, self.fonts, 'password')
        start_timer = pygame.time.get_ticks() # get the current time in milliseconds

        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.display_surface.blit(self.bg,(0,0))

            # draw sign up title text onto display surface with outline
            sign_up_text = Button(None, 
                                (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 5.5), "SIGN UP", self.get_font(125),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 3) # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            # create back button to return to main menu from this screen and update it so it still has hover effects like normal buttons
            signup_back_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), (105,35), 
                                      "BACK", self.get_font(50), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
        
            # create back button to return to main menu from this screen and update it so it still has hover effects like normal buttons
            create_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), 
                                    (WINDOW_WIDTH // 2 - 460, WINDOW_HEIGHT // 2 + 250), "CREATE", self.get_font(44), 
                                    COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)    

            login_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), 
                                    (WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 + 250), "LOGIN", self.get_font(44), 
                                    COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)    
            
            # draw username tag above position of username_textbox with outline
            username_label = Button(None,
                                    (WINDOW_WIDTH // 2 - 325, WINDOW_HEIGHT // 2 - 80), "USERNAME", self.get_font(64), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            # draw password tag below position of username elements with outline
            password_label = Button(None,
                                    (WINDOW_WIDTH // 2 - 325, WINDOW_HEIGHT // 2 + 80), "PASSWORD", self.get_font(64), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it
            
            # draw rules tag right of textboxes with outline
            checklist_label = Button(None,
                                    (WINDOW_WIDTH // 2 + 235, WINDOW_HEIGHT // 2 - 80), "CHECKLIST", self.get_font(64), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            username_length_label = Button(None,
                                    (WINDOW_WIDTH // 2 + 235, WINDOW_HEIGHT // 2 - 12), "- USERNAME BETWEEN 3-10 CHARACTERS", self.get_font(35), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            password_length_label = Button(None,
                                    (WINDOW_WIDTH // 2 + 235, WINDOW_HEIGHT // 2 + 56), "- PASSWORD BETWEEN 12-15 CHARACTERS", self.get_font(35), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            alphanumeric_label = Button(None,
                                    (WINDOW_WIDTH // 2 + 235, WINDOW_HEIGHT // 2 + 124), "- ALPHANUMERIC CHARACTERS", self.get_font(35), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            password_special_char_label = Button(None,
                                    (WINDOW_WIDTH // 2 + 235, WINDOW_HEIGHT // 2 + 192), "- PASSWORD CONTAINS SPECIAL CHAR", self.get_font(35), 
                                    COLORS['white'], COLORS['white'], COLORS['black'], 2) # # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [sign_up_text, signup_back_button, create_button, login_button, self.cog_button, username_label, password_label, 
                           username_length_label, password_length_label, alphanumeric_label, password_special_char_label, 
                           checklist_label]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            elapsed_time = pygame.time.get_ticks() - start_timer
            if elapsed_time > 10000: # after 5 seconds, switch to play screen
                return self.loading() # return used to fully break out of this loop, preventing infinite loops when switching between screens

            # event loop constantly run in this screen to check for quit or button clicks
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if signup_back_button.checkForInput(mouse_pos):
                        self.main_menu()
                    if self.cog_button.checkForInput(mouse_pos):
                        self.settings()
                    if create_button.checkForInput(mouse_pos):
                        
                        exists = self.db.user_exists(username_textbox.text)
                        if not exists:
                            self.db.register(username_textbox.text, password_textbox.text)
                            # green text saying registered!
                        else:
                            pass
                            # text saying account exists
                        
                    if login_button.checkForInput(mouse_pos):
                        login_status = self.db.login(username_textbox.text, password_textbox.text)
                        if login_status == True:
                            # login works text
                            self.username = username_textbox.text
                            self.userid = self.db.get_userid(username_textbox.text)
                            
                            trainers_defeated = self.db.get_trainers_defeated(self.userid)
                            # ["w0","u1","u2"]

                            for trainer in trainers_defeated:
                                TRAINER_DATA.get(trainer,[])
                            
                            
                            self.loading()
                        else:
                            pass
                            # say login dont work

            # update and check the input of all Textbox objects
            username_textbox.check_input(events)
            username_textbox.update()
            password_textbox.check_input(events)
            password_textbox.update()

            pygame.display.update()
            self.clock.tick(60)
    
    def loading(self):

        self.loading_width = 0

        while True:

            self.display_surface.blit(self.bg,(0,0))

            loading_text = Button(None, 
                                (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 15), "Loading Assets..", self.get_font(50),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 2) # made hover color for loading text white so visually, 
                                  # color doesn't change when mouse moves over it
            percentage = int((self.loading_width / (self.loading_container.width - 6)) * 100)
            percentage_text = Button(None, 
                                (WINDOW_WIDTH // 2, WINDOW_HEIGHT//2 + 135), f"{percentage}%", self.get_font(40),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 2) # made hover color for percentage text white so visually, 
                                  # color doesn't change when mouse moves over it
            
            # no hover effect needed for loading text or title, so just update directly without checking for hover
            for button in [loading_text, percentage_text, self.title]:
                button.update(self.display_surface)

            pygame.draw.rect(self.display_surface, COLORS['black'], self.loading_container, 0) # actually draw loading container (boundary box) onto display surface

            # create loading bar rectangle that will grow in width each frame, the - 6 is to account for 3 pixel border on each side of container
            loading_fill = pygame.Rect(self.loading_container.x + 3, self.loading_container.y + 3, self.loading_width, self.loading_container.height - 6) 
            pygame.draw.rect(self.display_surface, COLORS['white'], loading_fill)

            self.loading_width += 2

            if self.loading_width >= self.loading_container.width - 6: # when the loading bar is full, taking into consideration the padding
                return self.play() # return used to fully break out of this loop, preventing infinite loops when switching between screens

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            pygame.display.update()

            self.clock.tick(60)

    def play(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.transition_check()
            self.display_surface.fill(COLORS['black'])
            dt = self.clock.tick() / 1000  # delta time in milliseconds since last frame, used for frame rate independent movement

            if self.dialog_tree: self.dialog_tree.update() # check inputs and update DialogTree object in self.dialog_tree attribute if self.dialog_tree is not empty
            self.all_sprites.update(dt) 

            # function of sprite groups where it looks at all sprites in it, and updates them using their individual update methods (hence doesn't apply to sprites as 
            # they have no update method)
            self.all_sprites.draw(self.player.rect.center) # draw all sprites in the all_sprites group onto the display surface with method from groups.py

            # create back button to return to main menu from this screen and update it so it still has hover effects like normal buttons
            play_back_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), (105,35), 
                                      "BACK", self.get_font(50), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
            
            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [play_back_button, self.cog_button]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            # event loop constantly run in this screen to check for quit or button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if play_back_button.checkForInput(mouse_pos):
                        self.main_menu()
                    if self.cog_button.checkForInput(mouse_pos):
                        self.midway_settings = True
                        self.settings()
            
            if self.monster_index_open: self.monster_index.update(dt) # after all sprites have been drawn as the monster index tint must be drawn above it each frame
            if self.match != None: self.match.update(dt)
            self.encounter_timer.update()
            self.check_grass()
                
            self.input() # run the input method to perform dialogue operations
            self.tint_screen(dt)
            pygame.display.update()

    def leaderboard(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()

            self.display_surface.fill(COLORS['black']) # fill display surface with black color to clear previous screen and make it seem as if new screen created
            # draw text onto display surface to indicate which screen this is (temporary placeholder)
            leaderboard_surf = self.get_font(80).render("This is the \n LEADERBOARD screen", True, COLORS['white'])
            leaderboard_rect = leaderboard_surf.get_rect(center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.display_surface.blit(leaderboard_surf, leaderboard_rect)

            # create back button to return to main menu from this screen and update it so it still has hover effects like normal buttons
            leaderboard_back_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), (105,35), 
                                      "BACK", self.get_font(50), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)

            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [leaderboard_back_button, self.cog_button]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            # event loop constantly run in this screen to check for quit or button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if leaderboard_back_button.checkForInput(mouse_pos):
                        self.main_menu()
                    if self.cog_button.checkForInput(mouse_pos):
                        self.settings()
            
            pygame.display.update()

            self.clock.tick(60)

    def help(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.display_surface.blit(self.bg,(0,0))

            # draw arrow keys and mouse images onto display surface
            self.display_surface.blit(self.arrow_keys, (WINDOW_WIDTH//2 - 400, WINDOW_HEIGHT//2 - 100))
            self.display_surface.blit(self.mouse, (WINDOW_WIDTH//2 - 325, WINDOW_HEIGHT//2 + 100))

            # draw help title text and instructions onto display surface with outline
            help_text = Button(None, 
                                (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 5.5), "HELP", self.get_font(125),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 3) # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            arrow_keys_text = Button(None, 
                                (WINDOW_WIDTH // 2 + 220, WINDOW_HEIGHT // 2 - 40), "Arrows To Move!", self.get_font(50),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 2) # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            mouse_text = Button(None, 
                                (WINDOW_WIDTH // 2 + 220, WINDOW_HEIGHT // 2 + 170), "Mouse To Select Attacks!", self.get_font(50),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 2) # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            # create back button to return to main menu from this screen and update it so it still has hover effects like normal buttons
            help_back_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), (105,35), 
                                      "BACK", self.get_font(50), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)

            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [help_text, arrow_keys_text, mouse_text, help_back_button, self.script_button, self.cog_button]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            # event loop constantly run in this screen to check for quit or button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if help_back_button.checkForInput(mouse_pos):
                        self.main_menu()
                    if self.cog_button.checkForInput(mouse_pos):
                        self.settings()
                    # if script button clicked, go to game description screen
                    if self.script_button.checkForInput(mouse_pos):
                        self.game_description()
            
            pygame.display.update()

            self.clock.tick(60)

    def game_description(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.display_surface.blit(self.bg,(0,0))

            # draw large scroll image in which game description text will be written, onto display surface
            scroll_rect = self.scroll.get_rect(center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.display_surface.blit(self.scroll, scroll_rect)

            # draw game description text onto display surface at centre to fit within scroll image
            game_description = self.get_font(15).render(
            "You’re about to enter a world of adventure, \n" \
            "with you as the hero. Talk to people and explore \n" \
            "everything you find: towns, roads, and caves alike. \n" \
            "Gather clues and information wherever you can. \n" \
            "By helping others, and facing challenges, \n" \
            "new paths will unfold.\n" \
            "\n" \
            "You’ll meet rivals and encounter wild creatures \n" \
            "with the goal to capture them and win matches.\n" \
            "Stay strong and keep moving forward. Through \n" \
            "your journey, we hope that you will interact with \n" \
            "all sorts of people, achieving personal growth \n" \
            "cognitively and sharpening your abilities to \n" \
            "critically think. That is our biggest objective.\n \n" \
            "Press play, and let your adventure begin!", True, COLORS['black'])
            game_description_surf = game_description.get_rect(center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.display_surface.blit(game_description, game_description_surf)

            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [self.cog_button, self.script_button]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            # event loop constantly run in this screen to check for quit or button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.cog_button.checkForInput(mouse_pos):
                        self.settings()
                    # if script button clicked, go back to help screen to appear as if this screen is a sub-screen of help/a popup
                    if self.script_button.checkForInput(mouse_pos):
                        self.help()
            
            pygame.display.update()

            self.clock.tick(60)

    def settings(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.display_surface.blit(self.bg,(0,0))

            # draw settings title text onto display surface with outline
            settings_text = Button(None, 
                                (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 5.5), "SETTINGS", self.get_font(125),
                                  COLORS['white'], COLORS['white'], COLORS['black'], 3) # made hover color for settings text white so visually, 
                                  # color doesn't change when mouse moves over it

            # made hover color for settings text white so visually, color doesn't change when mouse moves over it as it is just a title
            music_text = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                                (WINDOW_WIDTH // 2 - 170, WINDOW_HEIGHT // 2 - 50), "MUSIC", self.get_font(74), COLORS['white'], COLORS['white'], COLORS['black'], 2)
            sfx_text = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                              (WINDOW_WIDTH // 2 - 170, WINDOW_HEIGHT // 2 + 70), "SFX", self.get_font(74), COLORS['white'], COLORS['white'], COLORS['black'], 2)
            battle_animations_text = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (400, 85)), 
                                            (WINDOW_WIDTH // 2 - 170, WINDOW_HEIGHT // 2 + 190), "BATTLE ANIM.", self.get_font(55), COLORS['white'], 
                                            COLORS['white'], COLORS['black'], 2)

            # creating text buttons which toggle settings on and off
            music_toggle_button = Button(None, (WINDOW_WIDTH // 2 + 200, WINDOW_HEIGHT // 2 - 50),
                                          self.music_on, self.get_font(64), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
            sfx_toggle_button = Button(None, (WINDOW_WIDTH // 2 + 200, WINDOW_HEIGHT // 2 + 70),
                                       self.sfx_on, self.get_font(64), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)
            battle_animations_toggle_button = Button(None, (WINDOW_WIDTH // 2 + 200, WINDOW_HEIGHT // 2 + 190),
                                                     self.battle_animations_on, self.get_font(64), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)

            # create back button to return to main menu from this screen and update it so it still has hover effects like normal buttons
            settings_back_button = Button(pygame.transform.scale(pygame.image.load("graphics/ui/button.png").convert_alpha(), (200, 60)), (105,35), 
                                      "BACK", self.get_font(50), COLORS['white'], COLORS['light-gray'], COLORS['black'], 2)

            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [settings_text, music_text, sfx_text, battle_animations_text, music_toggle_button,
                            sfx_toggle_button, battle_animations_toggle_button, settings_back_button]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            # event loop constantly run in this screen to check for quit or button clicks
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if settings_back_button.checkForInput(mouse_pos):
                        if self.midway_settings: # if coming from play method
                            # reset boolean flag to prevent the program from assuming the player is still returning from gameplay the next time we open settings
                            self.midway_settings = False
                            self.play() 
                        else:
                            self.main_menu()
                    # check if any of the toggle buttons have been clicked and update the text of the toggle buttons accordingly
                    if music_toggle_button.checkForInput(mouse_pos):
                        self.music_on = "OFF" if self.music_on == "ON" else "ON"
                    if sfx_toggle_button.checkForInput(mouse_pos):
                        self.sfx_on = "OFF" if self.sfx_on == "ON" else "ON"
                    if battle_animations_toggle_button.checkForInput(mouse_pos):
                        self.battle_animations_on = "LOW" if self.battle_animations_on == "HIGH" else "HIGH"
            
            pygame.display.update()

            self.clock.tick(60)

    # constantly draws and updates display surface with elements wanted
    def main_menu(self):
        while True:

            mouse_pos = pygame.mouse.get_pos()

            # sets ability to close program or click buttons
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.play_button.checkForInput(mouse_pos):
                        self.signup() # run the signup function if play button is clicked
                    if self.help_button.checkForInput(mouse_pos):
                        self.help() # run the help function if help button is clicked
                    if self.leaderboard_button.checkForInput(mouse_pos):
                        self.leaderboard() # run the leaderboard function if leaderboard button is clicked
                    if self.cog_button.checkForInput(mouse_pos):
                        self.settings() # run the settings function if settings button is clicked
                    if self.quit_button.checkForInput(mouse_pos):
                        pygame.quit() # run pygame's quit function if quit button is clicked, and exit program using sys.exit()
                        sys.exit()

            self.display_surface.blit(self.bg,(0,0))
            
            # iterate through all buttons to change color, update if hovered over or clicked to reduce code repetition
            for button in [self.play_button, self.help_button, self.leaderboard_button, self.quit_button, self.cog_button, self.title]:
                button.hover(mouse_pos)
                button.update(self.display_surface)

            pygame.display.update()
            self.clock.tick(60)



    # load tmx map using pytmx module
    def load_map(self):
        self.tmx_maps = tmx_import("data/maps")

        self.overworld_frames = {
            'water' : import_folder("graphics/tilesets/water"),
            'coast' : coast_import(24,12,"graphics/tilesets/coast"),
            # 8 terrain columns that are 3 tiles wide, and 4 rows that are 3 tiles wide means the arguments are cols = 24 and rows = 12
            'characters' : all_characters_import("graphics/characters")
        }
        self.monster_frames = {
            'icons' : import_folder_dict("graphics/icons"),
            'monsters' : monster_import(4, 2,"graphics/monsters"),
            # 4,2 as arguments as 4 columns and 2 rows. 1 row in tilemap file is idle frames, while other is attack frames
            'ui': import_folder_dict("graphics/ui"),
            'attacks': attack_importer("graphics/attacks")
        }

        self.fonts = {
            'dialog' : pygame.font.Font(("graphics/fonts/PixeloidSans.ttf"), 30), # dialog text at 30px size and Pixeloid Sans font
            'regular' : pygame.font.Font(("graphics/fonts/PixeloidSans.ttf"), 18), # regular text at 18px size and Pixeloid Sans font
            'small' : pygame.font.Font(("graphics/fonts/PixeloidSans.ttf"), 14), # small text at 14px size and Pixeloid Sans font
            'bold' : pygame.font.Font(("graphics/fonts/dogicapixelbold.otf"), 20), # bold text at 20px size and Dogica Pixel Bold font
            'title': pygame.font.Font("graphics/fonts/PixelifySans-Bold.ttf", 125),
            'credentials' : pygame.font.Font(("graphics/fonts/PixeloidSans.ttf"), 42)
        }

        self.match_bg_frames = import_folder_dict("graphics/backgrounds")
    
    # setup function to create sprites based on tmx map data
    def setup(self, tmx_map, player_start_pos):

        # clear map before drawing anything, whether it be a level transition, or the overworld itself
        for group in (self.all_sprites, self.collision_sprites, self.transition_sprites, self.character_sprites):
            group.empty()

        # these are the tile layers from the TMX map that we want to convert into sprite objects for rendering
        for layer in ['Terrain', 'Terrain Top']:
            # create a sprite for each tile and add it to all_sprites group
            for x,y, image in tmx_map.get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites, WORLD_LAYERS['bg']) # this will always be the background, so draw first
            # multiplied x and y tile coordinates by tile size to get pixel coordinates for each tile

        # objects object layer
        for object in tmx_map.get_layer_by_name('Objects'): # iterate through all objects in the tmx map
            if object.name == 'top':
                Sprite((object.x,object.y), object.image, self.all_sprites, WORLD_LAYERS['top'])
            else:
            # create sprite and add to all_sprites group so it can be drawn and updated to screen and to collision_sprites so collision logic can apply
                CollidableSprite((object.x,object.y), object.image, (self.all_sprites, self.collision_sprites))

        # transition object layer
        for object in tmx_map.get_layer_by_name('Transition'): # iterate through all the transition rectangles in the tmx map
            TransitionSprite((object.x, object.y), (object.width, object.height), (object.properties['target'], object.properties['pos']), self.transition_sprites)

        # grass objects in monsters object layer
        for object in tmx_map.get_layer_by_name('Monsters'): # iterate through all grasslands in the tmx map
            MonsterGrassSprite((object.x,object.y), object.image, (self.all_sprites, self.grass_sprites), object.properties['biome'], 
                               object.properties['monsters'], object.properties['level'])

        # entities object layer
        for object in tmx_map.get_layer_by_name('Entities'): # iterate through all entities in the tmx map
            if object.name == 'Player':
                if object.properties['pos'] == (player_start_pos):
                    # create player sprite at specified start position and add to all_sprites group and save it as attribute self.player
                    self.player = Player((object.x, object.y), self.overworld_frames['characters']['player'], (self.all_sprites),
                                         object.properties['direction'], collision_sprites = self.collision_sprites)
            else:
                NPC((object.x,object.y), self.overworld_frames['characters'][object.properties['graphic']], 
                    (self.all_sprites, self.collision_sprites, self.character_sprites), object.properties['direction'], 
                    TRAINER_DATA[object.properties['character_id']], nurse = object.properties['character_id'] == 'Nurse')

        # water object layer animation
        for object in tmx_map.get_layer_by_name('Water'): # iterate through all the water objects in the tmx map

            # iterate through the grid and split water into tile-sized positions to place animated frames

            # object.x + object.width is end x-coordinate of water area, so is end of the range for the for loop, and step by tile size to get x coordinates of the tile positions 
            for x in range(int(object.x), int(object.x + object.width), TILE_SIZE): # int casting as for loops need integer number of iterations
                # object.y + object.width is end y-coordinate of water area, so is end of the range for the for loop, and step by tile size to get y coordinate of the tile positions 
                for y in range(int(object.y), int(object.y + object.height), TILE_SIZE):
                    # create an AnimatedSprite at this area, at 'water' layer order
                    AnimatedSprite((x,y), self.overworld_frames['water'], self.all_sprites, WORLD_LAYERS['water']) # draw before background, like it is a base layer

        # coast object layer animation
        for object in tmx_map.get_layer_by_name('Coast'): # iterate through all the coast objects in the tmx map
            terrain = object.properties['terrain']
            side = object.properties['side']
            AnimatedSprite((object.x, object.y), self.overworld_frames['coast'][terrain][side], 
                           self.all_sprites, WORLD_LAYERS['bg']) # this will always be the background, so draw first
            
        # collisions object layer
        for object in tmx_map.get_layer_by_name('Collisions'): # iterate through all the collidable rectangle landscape objects in the tmx map
            BorderSprite((object.x,object.y), pygame.Surface((object.width, object.height)), self.collision_sprites)



    # transition system
    def transition_check(self):
        # check if player hitbox collides with transition areas
        sprites = [sprite for sprite in self.transition_sprites if sprite.rect.colliderect(self.player.hitbox)]
        # this selects every sprite in transition_sprites that are colliding with player, and stores in list
        if sprites:
            self.player.block()
            self.transition_target_properties = sprites[0].target
            self.tint_mode = 'tint'

    def tint_screen(self, dt):
        if self.tint_mode == 'untint':
            self.tint_progress -= self.tint_speed * dt # reduce opacity of screen

        if self.tint_mode == 'tint':
            self.tint_progress += self.tint_speed * dt
            if self.tint_progress >= 255: # max value of opacity, and in this case is pure black
                if type(self.transition_target_properties) == Match: # if going into a match, then also set the self.match attribute to not None
                    self.match = self.transition_target_properties
                elif self.transition_target_properties == 'overworld': # if going back from a match, reset self.match attribute to None so the battle screen disappears
                    self.match = None
                else: # usual behaviour
                    self.setup(self.tmx_maps[self.transition_target_properties[0]], self.transition_target_properties[1]) 
                # call setup again with the new tilemap to render and player_start_pos
                self.tint_mode = 'untint'
                self.transition_target_properties = None # reset for next time player goes to transition area or TransitionSprite object
        
        self.tint_progress = max(0, min(self.tint_progress, 255))

        self.tint_surf.set_alpha(self.tint_progress) # sets alpha value (transparacency) of surface
        self.display_surface.blit(self.tint_surf, (0,0))

    def input(self):
        if self.dialog_tree == None and self.match == None:
            keys = pygame.key.get_just_pressed() # pygame-ce feature to check if the key was pressed only once
            if keys[pygame.K_SPACE]: # if clicked key, implying they want to interact with background character
                for character in self.character_sprites:
                    if check_connection(100, self.player, character): # if player aligned on the axes, close enough to NPC, and faces it
                        self.player.block() # block player movement
                        character.change_direction(self.player.rect.center) # make NPC face player too
                        self.create_dialog(character)
        
            if keys[pygame.K_RETURN]:
                self.monster_index_open = not self.monster_index_open
                self.player.blocked = not self.player.blocked
    
    def create_dialog(self, character): # as the character is the one talking to the player
            if self.dialog_tree == None:
                self.dialog_tree = DialogTree(character, self.player, self.all_sprites, self.fonts['dialog'], self.del_dialog) 
            # any instance of DialogueTree must be in all_sprites, so it can be drawn to screen

    def del_dialog(self, character):
        self.dialog_tree = None # stop dialog being shown
        if character.nurse:
            for each_monster in self.player_monsters.values(): # make all the health and energy of player's tames to their maximum values
                each_monster.health = each_monster.get_stat('max_health')
                each_monster.energy = each_monster.get_stat('max_energy')
            self.player.unblock() # player can move again after dialog is complete
            
        elif not character.trainer_data['defeated']: 
            # if reached the end of a dialog with an NPC that hasn't been beat yet, then make transition's target the match,
            # so tint will perform a tinting effect AND move screen into battle's UI
            self.transition_target_properties = Match(self.player_monsters, character.trainer_monsters, self.monster_frames, 
                                                      self.match_bg_frames[character.trainer_data['biome']], self.fonts, self.end_match, character)
            # search the background frames for the required background image for this character's biome
            self.tint_mode = 'tint'
        else: # if NPC is not a nurse and it's defeated, then just end the dialog by unblocking player, and for consistency, setting its in_dialog attribute to False
            self.player.unblock()
            character.in_dialog = False # signals to program that the player is no longer in a dialog sequence and that the NPCs can move again

    def end_match(self, character, won):
        self.transition_target_properties = 'overworld'
        self.tint_mode = 'tint'
        if character: # if done fighting a character
            if won:
                character.trainer_data['defeated'] = True
                self.create_dialog(character)
            else: # lost
                self.player.unblock() # just unblock
        else: # if done fighting in a wild encounter
            self.player.unblock()

    def check_grass(self):
        if [sprite for sprite in self.grass_sprites if sprite.rect.colliderect(self.player.hitbox)] and not self.match and self.player.direction:
            # check player is in grass tiles, not already in a battle (to prevent overlapping battles), and is moving around
            if not self.encounter_timer.active: # if a timer has not already begun to spawn a battle in yet, then do it
                self.encounter_timer.start()

    def monster_encounter(self):
        sprites = [sprite for sprite in self.grass_sprites if sprite.rect.colliderect(self.player.hitbox)]
        if sprites and self.player.direction: # player still in grass and still moving after 2 seconds
            self.player.block()
            # retrieve monsters designated for this patch and setup a battle with them
            opponent_monsters = {index:Monster(monster, sprites[0].level) for index, monster in enumerate(sprites[0].monsters)}
            self.transition_target_properties = Match(self.player_monsters, opponent_monsters, self.monster_frames, 
                                                      self.match_bg_frames[sprites[0].biome], self.fonts, self.end_match, None)
            self.tint_mode = 'tint' # begin the transition into the match

# main game loop
if __name__ == '__main__':
    game = Game()
    game.main_menu() # start the main menu as the first screen to be executed

