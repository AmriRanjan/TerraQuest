from settings import *
from sprite import MonsterSprite, MonsterNameSprite, MonsterStatsSprite, MoveSprite, CrossSprite
from groups import MatchSprites
from game_data import ATTACK_DATA
from timer import Timer # import Timer class
from random import choice
from button import Button

class Match:
    def __init__(self, player_monsters, opponent_monsters, monster_frames, match_bg_surf, fonts, end_match, NPC, db, user_id, monster_ids, sounds):
        self.display_surface = pygame.display.get_surface() # surface for the battle UI to pop up on
        self.match_bg_surf = match_bg_surf
        self.monster_frames = monster_frames
        self.fonts = fonts
        self.monster_data = {'player': player_monsters, 'opponent': opponent_monsters} 
        # segregate the dictionaries for the player and opponent monsters in one central dictionary for easy access
        self.end_match = end_match
        self.NPC = NPC
        self.can_catch = self.NPC is None
        self.sounds = sounds

        self.match_sprites = MatchSprites() # a group for when changes need to be made to both the player and opponent monsters automatically, saving time
        self.player_sprites = pygame.sprite.Group() # separate group just for the player's monsters so we can modify them separately when wanted
        self.opponent_sprites = pygame.sprite.Group() # separate group just for the opponent's monsters so we can modify them separately when wanted
        
        # INTERACTIVITY
        self.current_active_monster = None # to keep track of which monster is currently active
        self.selection_mode = None
        self.selection_move = None # to keep track of which attack is selected at the moment
        self.selection_team = 'player' # to keep track of whose turn it is to select an action
        self.indexes = {
            # value is 0 at start, meaning the first option in the general menu is selected by default and the same applies for the rest
            'general_index': 0,
            'available_moves_index': 0,
            'target_index': 0
        }

        self.timers = {
            'opponent_delay': Timer(600, func = self.opponent_move) # delay in milliseconds before opponent makes a move
        }

        # TEXT INITIALISATION
        self.title = None
        self.description = None

        # DATABASE INITIALISATION
        self.db = db
        self.userid = user_id
        self.monster_ids = monster_ids # hold the monster_id of each monster so health and energy and xp changes can be made to database

        self.setup()

    def setup(self):
        for entity, dict_monsters in self.monster_data.items():
            for index, each_monster in {key:value for key, value in dict_monsters.items() if key <= 2}.items(): # only get the data for the first 3 Monster objects 
                self.create_monster(each_monster, index, index, entity)

    def create_monster(self, monster, index, pos_index, entity): # separate method to separate the logic of creating and killing monsters from the screen
        monster.paused = False # as soon as a battle begins, as the end of a previous battle set the readiness on halt, begin it again for this new match
        frames = self.monster_frames['monsters'][monster.name]
        if entity == 'player':
            match_positions_list = list(BATTLE_POSITIONS['left'].values())
            pos = match_positions_list[pos_index]
            groups = (self.match_sprites, self.player_sprites) # groups for the MonsterSprite object to be appended to for drawing and updating
            frames = {state: [pygame.transform.flip(frame, True, False) for frame in frames] for state, frames in frames.items()} # flip the frames for player's monsters
        else:
            match_positions_list = list(BATTLE_POSITIONS['right'].values())
            pos = match_positions_list[pos_index]
            groups = (self.match_sprites, self.opponent_sprites) # groups for the MonsterSprite object to be appended to for drawing and updating

        monster_sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity, self.apply_move) 
        # create a new sprite for each of the monsters in the match UI

        # NAME
        name_pos = monster_sprite.rect.midleft + vector(16, -70)
        MonsterNameSprite(name_pos, monster_sprite, self.match_sprites, self.fonts['regular']) 
        # created a name sprite for each monster and added it to the match_sprites group

        # STATS
        MonsterStatsSprite(monster_sprite.rect.midbottom + vector(0, 20), monster_sprite, (150, 48), self.match_sprites, self.fonts['small'])
        # created a stats sprite for each monster and added it to the match_sprites group

    def input(self):
        if self.selection_mode != None: # only check for input if in selection mode
            keys = pygame.key.get_just_pressed()

            if self.selection_mode == 'general_index':
                limiter = len(BATTLE_CHOICES['full'] if self.can_catch else BATTLE_CHOICES['limited'])
                # if in general selection mode, limit to number of general options which is length of BATTLE_CHOICES['full']
            if self.selection_mode == 'available_moves_index':
                limiter = len(self.current_active_monster.monster.get_abilities(all_wanted = False))
                # if in available moves selection mode, limit to number of available moves for the active monster
            if self.selection_mode == 'target_index':
                limiter = len(self.opponent_sprites) if self.selection_team == 'opponent' else len(self.player_sprites) 
                # find how many monsters are on the targeted side at every frame as this number may change during the match due
                # to some getting knocked out and hence removed from match UI

            if keys[pygame.K_DOWN]:
                self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] + 1) % limiter # wrap around using modulo operator

            if keys[pygame.K_UP]:
                self.indexes[self.selection_mode] = (self.indexes[self.selection_mode] - 1) % limiter # wrap around using modulo operator

            if keys[pygame.K_SPACE]:
                if self.selection_mode == 'target_index':
                        target_sprite_group = self.opponent_sprites if self.selection_team == 'opponent' else self.player_sprites
                        sprites = {sprite.pos_index: sprite for sprite in target_sprite_group.sprites()}
                        # creates a dictionary that maps pos_index to sprite for easy access to the selected target sprite
                        target_sprite = sprites[list(sprites.keys())[self.indexes['target_index']]] 
                        # get the pos_index key at the current target_index and use that to get the corresponding sprite from sprites dictionary

                        if self.selection_move:
                            self.current_active_monster.activate_move(target_sprite, self.selection_move)
                            self.selection_mode, self.current_active_monster, self.selection_move = None, None, None 
                            # reset selected move, active monster and selection mode after attack is executed for the next turn's move selection
                        else: # no move selected, so must be the catching option
                            if target_sprite.monster.health < target_sprite.monster.get_stat('max_health') * 0.3: 
                                # can only successfully catch if target monster's health is below 30%
                                index = len(self.monster_data['player'])
                                self.monster_data['player'][index] = target_sprite.monster 
                                # add the unique instance of Monster, with all its details, to monster index so the exact same monster is added to player's collection
                                self.monster_ids.append(self.db.add_monster(self.userid, target_sprite.monster.name, target_sprite.monster.level, 0, 
                                                                            target_sprite.monster.health, target_sprite.monster.energy))
                                self.update_all_monsters('unpaused')
                                target_sprite.kill() # remove the monster sprite from its groups to stop it being drawn and updated in match - it has been captured
                                self.selection_mode = None
                            else:
                                CrossSprite(target_sprite.rect.center, self.monster_frames['ui']['cross'], self.match_sprites, 900)
                                self.update_all_monsters('unpaused')

                if self.selection_mode == 'available_moves_index':
                    self.selection_mode = 'target_index'
                    # move to target selection mode after clicking spacebar on the attack index, suggesting an attack has been selected
                    self.selection_move = self.current_active_monster.monster.get_abilities(all_wanted = False)[self.indexes['available_moves_index']]
                    self.selection_team = ATTACK_DATA[self.selection_move]['target'] # get the side that the selected attack targets

                if self.selection_mode == 'general_index':
                    if self.indexes['general_index'] == 0: # if attack is selected
                        self.selection_mode = 'available_moves_index'
                    
                    if self.indexes['general_index'] == 1: # if defense is selected
                        self.update_all_monsters('unpaused') 
                        # unpause all monsters so all the monsters can increase readiness attributes again, 
                        # and the next monster can take its turn - the process begins all over again
                        self.current_active_monster, self.selection_mode = None, None # reset active monster and selection mode
                        self.indexes['general_index'] = 0 # reset the general index to default
                    
                    if self.indexes['general_index'] == 2: # if catch is selected
                        self.selection_mode = 'target_index'
                        self.selection_team = 'opponent' # catching can only be done on opponent's monsters by the user
                    
                    self.indexes = {key: 0 for key in self.indexes} # reset all indexes to 0 after confirming a selection

            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ('available_moves_index', 'target_index'):
                    self.selection_mode = 'general_index' # go back to general selection mode

    def check_active(self):
        for each_monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites(): # check both player and opponent monsters
            if each_monster_sprite.monster.readiness >= 100:
                self.update_all_monsters('paused') # pause all monsters when one monster is active
                each_monster_sprite.monster.readiness = 0
                self.current_active_monster = each_monster_sprite
                if self.player_sprites in each_monster_sprite.groups(): # check if the active monster is a player monster
                    self.selection_mode = 'general_index' # enter selection mode for player to choose action
                else:
                    self.selection_mode = None
                    self.selection_move = None
                    self.selection_team = 'player'
                    self.timers['opponent_delay'].start() # start the timer for opponent's action delay

    def update_all_monsters(self, state):
        for each_monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites(): # check both player and opponent monsters
            # pause or unpause all monsters based on the state given
            if state == 'paused':
                each_monster_sprite.monster.paused = True
            else:
                each_monster_sprite.monster.paused = False

    def update_timers(self):
        for timer in self.timers.values():
            timer.update() # check if each timer has finished and run its function if so

    def apply_move(self, target_sprite, move, amount):
        # animation
        MoveSprite(target_sprite.rect.center, self.monster_frames['attacks'][ATTACK_DATA[move]['animation']], self.match_sprites)
        # each frame of the attack animation is blitted at the center of the target monster
        self.sounds[ATTACK_DATA[move]['animation']].play()

        # dealing damage, considering defense stat of target and type advantages
        move_element = ATTACK_DATA[move]['element'] # element of the move being used
        target_type = target_sprite.monster.monster_type # element of the target monster

        if move_element == 'fire' and target_type == 'plant' or\
        move_element == 'water' and target_type == 'fire' or\
        move_element == 'plant' and target_type == 'water':
            amount *= 1.5 # super effective

        if move_element == 'fire' and target_type == 'water' or\
        move_element == 'water' and target_type == 'plant' or\
        move_element == 'plant' and target_type == 'fire':
            amount *= 0.5 # not very effective

        target_defense = 1 - target_sprite.monster.get_stat('defense') / (target_sprite.monster.get_stat('defense') + 2500) # defense multiplier formula
        amount *= target_defense # reduce damage based on target's defense stat

        # update target's health
        max_hp = target_sprite.monster.get_stat('max_health')
        target_sprite.monster.health = max(0, min(target_sprite.monster.health - amount, max_hp))

        self.check_fainted()

        # resume game
        self.update_all_monsters('unpaused') # unpause all monsters so all the monsters can increase readiness attributes again, 
        # and the next monster can take its turn - the process begins all over again

    def check_fainted(self):
        for each_monster_sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites(): # check both player and opponent monsters
            if each_monster_sprite.monster.health <= 0:
                if self.player_sprites in each_monster_sprite.groups():
                    each_monster_sprite.kill() # remove the monster sprite from all groups it belongs to
                else:
                    each_monster_sprite.kill() # remove the monster sprite from all groups it belongs to
                    xp_amount = each_monster_sprite.monster.level * 100/len(self.player_sprites) # simple XP formula based on level and number of player's monsters
                    for player_monster_sprite in self.player_sprites.sprites():
                        player_monster_sprite.monster.gain_xp(xp_amount) # give each of the player's monsters some XP when an opponent monster faints

    def draw_ui(self):
        if self.current_active_monster: # only draw the UI if there is an active monster
            if self.selection_mode == 'general_index':
                self.draw_general()
            if self.selection_mode == 'available_moves_index':
                self.draw_attack_moves()
            if self.selection_mode == 'target_index':
                self.draw_indicator()

    def draw_indicator(self):
        # draw target indicator over the current targeted monster
        target_sprite_group = self.opponent_sprites if self.selection_team == 'opponent' else self.player_sprites
        target_sprites = {sprite.pos_index: sprite for sprite in target_sprite_group.sprites()}
        if target_sprites:  # ensure there are sprites
            target_sprite = target_sprites[list(target_sprites.keys())[self.indexes['target_index']]] # chosen target_sprite MonsterSprite object for a move to be landed
            target_icon = self.monster_frames['ui']['notice'] # image depicting it is selected at the moment
            icon_rect = target_icon.get_frect(midbottom=target_sprite.rect.midtop + vector(0, 14)) 
            # place image above the target_sprite but closeby via the (0, 6) vector offset
            self.display_surface.blit(target_icon, icon_rect)

    def draw_general(self):
        choices = BATTLE_CHOICES['full'] if self.can_catch else BATTLE_CHOICES['limited'] # less options allowed if monster cannot be caught
        for index, (option, data_dict) in enumerate(choices.items()): # get each option and its data dictionary
            if index == self.indexes['general_index']: # check if the current option is the selected one
                surf = self.monster_frames['ui'][f"{data_dict['icon']}_highlight"] # search the active icon frames from the ui frames
            else:
                surf = pygame.transform.grayscale(self.monster_frames['ui'][data_dict['icon']]) # search the icon frames from the ui frames
            rect = surf.get_frect(center = self.current_active_monster.rect.midright + data_dict['pos']) # position the icons relative to the active monster
            self.display_surface.blit(surf, rect)

    def draw_attack_moves(self):
        abilities = self.current_active_monster.monster.get_abilities(all_wanted = False) # only get abilities that can be used based on current energy
        width = 150
        height = 200
        visible_attacks_at_once = 4
        item_height = height/visible_attacks_at_once
        vertical_offset = 0 if self.indexes['available_moves_index'] < visible_attacks_at_once else -(self.indexes['available_moves_index'] - visible_attacks_at_once + 1) * item_height
        # amount of rows in pixels to move item rectangles up or down by

        bg_rect = pygame.FRect((0,0), (width, height)).move_to(midleft = self.current_active_monster.rect.midright + vector(20, 0))
        # create a background rectangle for the list of abilities that is moved to the right of the active monster with some padding
        pygame.draw.rect(self.display_surface, COLORS['white'], bg_rect) # white rectangle background

        for index, ability in enumerate(abilities):
            selected = index == self.indexes['available_moves_index'] # check if the current ability we are on is the selected one and store as boolean in selected

            if selected:
                type = ATTACK_DATA[ability]['element']
                if type != 'normal':
                    text_color = COLORS[type] # color the text based on the ability's element type if selected over
                else:
                    text_color = COLORS['black']
            else:
                text_color = COLORS['light']
            text_surf = self.fonts['regular'].render(ability, True, text_color)

            text_rect = text_surf.get_frect(center = bg_rect.midtop + vector(0, item_height/2 + index * item_height + vertical_offset))
            # position each ability centrally within bg_rect, spaced out vertically based on item_height

            if bg_rect.collidepoint(text_rect.center): # only draw the text if it is within the background rectangle
                self.display_surface.blit(text_surf, text_rect)

    def opponent_move(self):

        abilities = self.current_active_monster.monster.get_abilities(all_wanted = False) # all the abilities of the opponent AI monster

        # setting up values
        best_ability = None
        best_target = None
        best_score = float("-inf")

        for move in abilities: # go through every move in the abilities for this creature, and extract useful data for evaluation
            move_data = ATTACK_DATA[move]
            move_target_side = move_data['target']
            move_element = move_data['element']
            move_cost = move_data['cost']
            cost_penalty = 0.15 * move_cost

            # CONSIDERING HEAL MOVES
            if move_target_side == 'player':
                for each_monster_sprite in self.opponent_sprites.sprites():
                    hp = each_monster_sprite.monster.health
                    max_hp = each_monster_sprite.monster.get_stat('max_health')
                    hp_ratio = hp / max_hp 
                    missing = max_hp - hp
                    # calculated values that influence whether monster should be healed or not

                    # only consider health moves if it is not already on high health
                    if hp_ratio < 0.8:
                        emergency_bonus = 40 if hp_ratio < 0.2 else 0 
                        # huge bonus if the health of any AI monsters reach 20% or lower, to increase the chance of a healing move being selected at this moment
                        score = missing + emergency_bonus - cost_penalty

                        if score > best_score: # if this move is better than what we have currently stored for the best_ability, then this is the new best choice
                            best_score = score
                            best_ability = move
                            best_target = each_monster_sprite

            # CONSIDERING ATTACK MOVES
            if move_target_side == 'opponent':
                for target_sprite in self.player_sprites.sprites():
                    target_type = target_sprite.monster.monster_type # type of target_sprite (player monster) we are iterating over

                    type_multiplier = 1
                    
                    if  move_element == 'fire' and target_type == 'plant' or \
                        move_element == 'water' and target_type == 'fire' or \
                        move_element == 'plant' and target_type == 'water':
                        type_multiplier = 1.5 # super effective

                    if  move_element == 'fire' and target_type == 'water' or \
                        move_element == 'water' and target_type == 'plant' or \
                        move_element == 'plant' and target_type == 'fire':
                        type_multiplier = 0.5 # not very effective

                    defense_multiplier = 1 - target_sprite.monster.get_stat('defense') / (target_sprite.monster.get_stat('defense') + 2500) # defense multiplier formula

                    base = self.current_active_monster.monster.get_base_damage(move)
                    predicted_damage = base * type_multiplier * defense_multiplier 
                    # find the usual damage that would be rendered for this move, from this monster, to the target_sprite

                    knockout_bonus = 200 if predicted_damage >= target_sprite.monster.health else 0 
                    # huge weighting if there is a move that instantly can defeat a player monster

                    # factoring in type advantages
                    score = ((predicted_damage + knockout_bonus) * type_multiplier) - cost_penalty # score for this move

                    if score > best_score: # if this move is better than what we have currently stored for the best_ability, then this is the new best choice
                        best_score = score
                        best_ability = move
                        best_target = target_sprite

        self.current_active_monster.activate_move(best_target, best_ability)

    def check_end_match(self):
        # rivals have been defeated
        if len(self.opponent_sprites) == 0:
            self.update_all_monsters('paused') # pause all monsters when match ends to avoid further actions to prevent index errors
            for monster in self.monster_data['player'].values():
                monster.readiness = 0 # reset readiness of all player's monsters after winning for next match to correctly begin from the start
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 50, 50, 100)) # last value is 100 to signify slightly transparent, but mostly dimmed screen
            self.display_surface.blit(overlay, (0, 0)) 
            self.title = Button(None, 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2), "YOU WON!", self.fonts['title'], COLORS['white'], COLORS['white'], COLORS['black'], 3)
                             # made hover color for title white so visually, color doesn't change when mouse moves over it
            self.description = Button(None, 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30), "LEADERBOARD SCORE + 1", self.fonts['dialog'], COLORS['white'], COLORS['white'], COLORS['black'], 3)
                             # made hover color for title white so visually, color doesn't change when mouse moves over it
            self.title.update(self.display_surface)
            self.description.update(self.display_surface)
            self.end_match(self.NPC, won = True)

        # user has been defeated
        if len(self.player_sprites) == 0:
            self.update_all_monsters('paused') # pause all monsters when match ends to avoid further actions to prevent index errors
            for monster in self.monster_data['player'].values():
                monster.readiness = 0 # reset readiness of all player's monsters after winning for next match to correctly begin from the start
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 50, 50, 100)) # last value is 100 to signify slightly transparent, but mostly dimmed screen
            self.display_surface.blit(overlay, (0, 0)) 
            self.title = Button(None, 
                            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2), "YOU LOST!", self.fonts['title'], COLORS['white'], COLORS['white'], COLORS['black'], 3)
                             # made hover color for title white so visually, color doesn't change when mouse moves over it
            self.title.update(self.display_surface)
            self.end_match(self.NPC, won = False)

    def update(self, dt): # actually update the screen for changes to be visible
        self.input()
        self.update_timers()
        self.display_surface.blit(self.match_bg_surf, (0,0))
        self.match_sprites.update(dt) # run all the commands in the MonsterSprite's update method, for each and every MonsterSprite object in match_sprites
        self.match_sprites.draw() # draw the sprites above the horizon

        self.check_active() # check if any monster is active to pause others
        self.draw_ui() # draw the battle UI elements on top of everything else
        self.check_end_match() # check if the match has ended
