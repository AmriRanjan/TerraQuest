from settings import *
from support import draw_stats_bars
from game_data import MONSTER_DATA, ATTACK_DATA

class MonsterIndex:
    def __init__(self, monsters, fonts, monster_frames):
        self.display_surface = pygame.display.get_surface()
        self.fonts = fonts
        self.monsters = monsters

        self.icon_images = monster_frames['icons']
        self.monster_images = monster_frames['monsters']
        self.frame_index = 0

        self.monster_index_tint = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT)) # size of tint surface
        self.monster_index_tint.set_alpha(200) # slightly transparent, but mostly dark screen

        self.main_index_rect = pygame.FRect(0,0, WINDOW_WIDTH * 0.6, WINDOW_HEIGHT * 0.8).move_to(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        # pygame.Frect specifies left side, top side, width and height of a rectangle

        self.visible_items = 5
        self.list_width = self.main_index_rect.width * 0.3
        # each monster in sidebar is given equal space by dividing height of bar by number of items that can be viewed at once
        self.item_height = self.main_index_rect.height / self.visible_items
        self.index = 0
        self.selected_index = None

        self.max_stats = {}
        for each_monster in MONSTER_DATA.values(): # get only the nested dictionary for every monster
            # in that nested dictionary, retrieve only the 'stats' dictionary inside it, and find all item (key-value) pairs inside
            for stat, value in each_monster['stats'].items():
                if stat != 'element':
                    # if the key does not have an entry already in max_stats attribute, then add the current key-value pair we are iterating over, inside of it
                    if stat not in self.max_stats: 
                        self.max_stats[stat] = value
                    # if the key does have an entry, then only replace the key-value pair for that stat in max_stats, 
                    # if the value in the current key-value pair is larger than the value stored
                    else:
                        if value > self.max_stats[stat]:
                            self.max_stats[stat] = value

        self.max_stats['health'] = self.max_stats.pop('max_health')
        self.max_stats['energy'] = self.max_stats.pop('max_energy')

    def input(self):
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_UP]:
            self.index -= 1
        if keys[pygame.K_DOWN]:
            self.index += 1
        if keys[pygame.K_SPACE]:
            if self.selected_index != None:
                # switch positions and keys of last two clicked monsters
                selected_monster = self.monsters[self.selected_index]
                current_monster = self.monsters[self.index]
                self.monsters[self.index] = selected_monster
                self.monsters[self.selected_index] = current_monster
                self.selected_index = None # reset for next swapping if ever needed
            else:
                self.selected_index = self.index

        self.index = self.index % len(self.monsters)

    def display_list(self):
        if self.index < self.visible_items:
            vertical_offset = 0
        else:
            vertical_offset = -(self.index - self.visible_items + 1) * self.item_height # amount of rows in pixels to move item rectangles up or down by

        for index, monster in self.monsters.items():

            item_rect_color = COLORS['gray'] if self.index != index else COLORS['light'] # unique colour for the currently chosen monster 
            text_color = COLORS['white'] if self.selected_index != index else COLORS['gold']

            # top of each item rectangle in sidebar list moves down the window (by increasing y value by same amount each time)
            top = self.main_index_rect.top + (index * self.item_height) + vertical_offset
            item_rect = pygame.FRect(self.main_index_rect.left, top, self.list_width, self.item_height)

            name_text_surf = self.fonts['regular'].render(monster.name, False, text_color) # obtain name for each monster in a regular font from self.fonts attribute
            name_text_rect = name_text_surf.get_frect(midleft = item_rect.midleft + vector(90,0)) # small offset vector to position it slightly right of halfway

            monster_icon_surf = self.icon_images[monster.name] # image for the current monster we are iterating over
            monster_icon_rect = monster_icon_surf.get_frect(center = item_rect.midleft + vector(45,0)) # between name and left edge

            if item_rect.colliderect(self.main_index_rect):
                pygame.draw.rect(self.display_surface, item_rect_color, item_rect) # print base layer rectangles of sidebar
                self.display_surface.blit(name_text_surf, name_text_rect)
                self.display_surface.blit(monster_icon_surf, monster_icon_rect)

        # shadow surface
        shadow_surf = pygame.Surface((4, self.main_index_rect.height))
        shadow_surf.set_alpha(100)
        self.display_surface.blit(shadow_surf,(self.main_index_rect.left + self.list_width -4, self.main_index_rect.top))

    def display_main(self, dt):
        monster = self.monsters[self.index]

        # main bg
        rect = pygame.FRect(self.main_index_rect.left + self.list_width, self.main_index_rect.top, 
                            self.main_index_rect.width - self.list_width, self.main_index_rect.height) # left, top, width and height parameters for FRect
        pygame.draw.rect(self.display_surface, COLORS['dark'], rect)

        # monster enlarged image
        enlarged_rect = pygame.FRect(rect.topleft, (rect.width, rect.height * 0.4)) # was possible to specify a position and size as a tuple,
        # instead of top, left, width, height arguments, to keep code concise
        pygame.draw.rect(self.display_surface, COLORS[monster.monster_type], enlarged_rect)

        # monster animation
        self.frame_index += ANIMATION_SPEED * dt # constantly changing frame index that is framerate independent
        monster_surf = self.monster_images[monster.name]['idle'][int(self.frame_index) % len(self.monster_images[monster.name]['idle'])] 
        # int casting as when multiplying by dt, self.frame_index can become a float, and floats cannot slice or index data structures
        monster_rect = monster_surf.get_frect(center = enlarged_rect.center)
        self.display_surface.blit(monster_surf, monster_rect)

        # name, level and type
        name_surf = self.fonts['bold'].render(monster.name, False, COLORS['white'])
        name_rect = name_surf.get_frect(topleft = enlarged_rect.topleft + vector(10, 10)) 
        # offset a little from the edges to make it seem like there is a padding
        self.display_surface.blit(name_surf, name_rect)

        level_surf = self.fonts['regular'].render(f'Lvl: {monster.level}', False, COLORS['white']) 
        # f-string to combine fixed string value with a changing variable to concatenate to it
        level_rect = level_surf.get_frect(bottomleft = enlarged_rect.bottomleft + vector(10, -10)) 
        # offset a little from the edges to make it seem like there is a padding
        self.display_surface.blit(level_surf, level_rect)

        monster_type_surf = self.fonts['regular'].render(monster.monster_type, False, COLORS['white'])
        monster_type_rect = monster_type_surf.get_frect(bottomright = enlarged_rect.bottomright + vector(-10, -10)) 
        # offset a little from the edges to make it seem like there is a padding
        self.display_surface.blit(monster_type_surf, monster_type_rect)

        # level bar
        draw_stats_bars(
            surface = self.display_surface,
            rect = pygame.FRect(level_rect.bottomleft, (100, 4)),
            value = monster.xp, # value is current exp
            max_value = monster.level_up_xp, # end of bar is the level up exp. If they get to end of bar, then level up happens
            color = COLORS['white'],
            bg_color = COLORS['dark']
        )

        # health and energy bars information
        bar_data = {
            'width': rect.width * 0.45,
            'height': 30,
            'top': enlarged_rect.bottom + rect.width * 0.03,
            'left': rect.left + rect.width / 4,
            'right': rect.left + rect.width * 3/4
        }

        healthbar_rect = pygame.FRect((0,0), (bar_data['width'], bar_data['height'])).move_to(midtop = 
                        (bar_data['left'], bar_data['top'])) # width and height obtained from dictionary
        draw_stats_bars(self.display_surface, healthbar_rect, monster.health, monster.get_stat('max_health'), COLORS['red'], COLORS['black'])
        # value is current health, while end of bar is the maximum health.
        hp_text = self.fonts['regular'].render(f"HP: {int(monster.health)}/{int(monster.get_stat('max_health'))}", False, COLORS['white'])
        # show fraction of the current health over the total health
        hp_rectangle = hp_text.get_frect(midleft = healthbar_rect.midleft + vector(10,0))
        self.display_surface.blit(hp_text, hp_rectangle) 

        energybar_rect = pygame.FRect((0,0), (bar_data['width'], bar_data['height'])).move_to(midtop = 
                        (bar_data['right'], bar_data['top'])) # width and height obtained from dictionary
        draw_stats_bars(self.display_surface, energybar_rect, monster.energy, monster.get_stat('max_energy'), COLORS['blue'], COLORS['black'])
        # value is current energy, while end of bar is the maximum energy.
        ep_text = self.fonts['regular'].render(f"EP: {int(monster.energy)}/{int(monster.get_stat('max_energy'))}", False, COLORS['white'])
        # show fraction of the current energy over the total energy
        ep_rectangle = hp_text.get_frect(midleft = energybar_rect.midleft + vector(10,0))
        self.display_surface.blit(ep_text, ep_rectangle)

        # all the information for smaller stats
        sides = {'left': healthbar_rect.left, 'right' : energybar_rect.left}
        info_height = rect.bottom - healthbar_rect.bottom



        # small stat bars
        stats_rect = pygame.FRect(sides['left'], healthbar_rect.bottom, healthbar_rect.width, info_height).inflate(0, -60) 
        # deflated stats_rect's height to give a bit of padding and distance between healthbar_rect and this section
        stats_text_surf = self.fonts['regular'].render('Stats', False, COLORS['white'])
        stats_text_rect = stats_text_surf.get_frect(bottomleft = stats_rect.topleft)
        self.display_surface.blit(stats_text_surf, stats_text_rect)

        monster_stats = monster.get_stats() # stats for the current monster in a dictionary

        stat_height = stats_rect.height / len(monster_stats) 
        # divided the stat space available by the number of stats in monster_stats, to hold the height available for each mini stat bar 

        for index, (stat, value) in enumerate(monster_stats.items()): # go through every stat FOR THIS monster at its level
            single_stat_rect = pygame.FRect(stats_rect.left, stats_rect.top + index * stat_height, stats_rect.width, stat_height)
            
            # text for every stat
            text_surf = self.fonts['regular'].render(stat, False, COLORS['white'])
            text_rect = text_surf.get_frect(midleft = single_stat_rect.midleft)
            self.display_surface.blit(text_surf, text_rect)

            bar_rect = pygame.FRect((text_rect.left, text_rect.bottom + 2), (single_stat_rect.width * 0.9, 4)) 
            # bar for each of its stats are slightly below text, to provide padding
            draw_stats_bars(self.display_surface, bar_rect, value, self.max_stats[stat] * monster.level, COLORS['white'], COLORS['black'])
            # use our utility function to render the stat bar, with max_value being the highest possible value for this stat at the monster’s current level



        # abilities and moves
        ability_rect = stats_rect.copy().move_to(left = sides['right']) # below the start of the energy bar
        ability_text_surf = self.fonts['regular'].render('Abilities', False, COLORS['white'])
        ability_text_rect = ability_text_surf.get_frect(bottomleft = ability_rect.topleft)
        self.display_surface.blit(ability_text_surf, ability_text_rect)

        for index, ability in enumerate(monster.get_abilities()): 
            # get what number of ability we are on, and its name. The index helps in positioning them in a vertically stacked format

            attack_type = ATTACK_DATA[ability]['element']

            text_surf = self.fonts['regular'].render(ability, False, COLORS['black']) # name of each attack
            # y-coordinate of every move box is 20px below top edge of ability_rect, and 20px afar from every other ability too
            y = 20 + ability_rect.top + index * (text_surf.get_height() + 20)
            single_ability_rect = text_surf.get_frect(topleft = (ability_rect.left,y))
            # draw single_ability_rect rectangle (in its position specified) to the window in a white color. 0px border argument, but a 4px rounded border
            pygame.draw.rect(self.display_surface, COLORS[attack_type], single_ability_rect.inflate(10,10), 0, 4)
            self.display_surface.blit(text_surf, single_ability_rect)

    def update(self, dt):
        self.input()
        self.display_surface.blit(self.monster_index_tint, (0,0)) # slightly darken background of game
        pygame.draw.rect(self.display_surface, 'black', self.main_index_rect) # print base layer of the monster index
        self.display_list() 
        self.display_main(dt) # dt obtained from play method in main.py where this is update method is run

