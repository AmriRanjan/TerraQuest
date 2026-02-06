# no importing pygame - can just be a normal python file as it only stores data. 
from game_data import ATTACK_DATA, MONSTER_DATA # import from its respective file
from random import randint

class Monster:
    def __init__(self, name, level):
        self.name = name
        self.level = level

        self.monster_type = MONSTER_DATA[self.name]['stats']['element'] # just a string holding its element
        self.monster_base_stats = MONSTER_DATA[self.name]['stats'] # stats are in a dictionary now
        self.health = self.monster_base_stats['max_health'] * self.level
        # multiply the health possible for a Monster object by its level. This makes sure more high level, experienced battlers are stronger
        self.energy = self.monster_base_stats['max_energy'] * self.level
        self.abilities = MONSTER_DATA[name]['abilities']

        # experience
        self.xp = 0 # experience starts at 0
        self.level_up_xp = self.level * 150 # the experience required to reach the next level scales with the monster’s current level

        # readiness
        self.readiness = 0 # readiness starts at 0 and builds up over time in battle
        self.paused = False # represents whether the monster is frozen (e.g. by a status effect) and so doesn't gain readiness

    def get_stat(self, specific_stat):
        return self.monster_base_stats[specific_stat] * self.level # maximum value for a statistic

    def get_stats(self): # return all the stats of the monster in a dictionary, having multiplied by their level first
        return {
            'health': self.get_stat('max_health'),
            'energy': self.get_stat('max_energy'),
            'attack': self.get_stat('attack'),
            'defense': self.get_stat('defense'),
            'speed': self.get_stat('speed'),
            'recovery': self.get_stat('recovery')
        }

    def get_abilities(self, all_wanted = True):
        if all_wanted:
            return [ability for lvl, ability in self.abilities.items() if self.level >= lvl]
        else:
            return [ability for lvl, ability in self.abilities.items() if self.level >= lvl and ATTACK_DATA[ability]['cost'] <= self.energy]
            # return only abilities that can be used based on current energy

    def get_info(self):
        # return current and maximum values of health, energy and readiness as tuples within a larger tuple
        return (
            (self.health, self.get_stat('max_health')),
            (self.energy, self.get_stat('max_energy')),
            (self.readiness, 100)
        )

    def reduce_energy(self, move):
        self.energy -= ATTACK_DATA[move]['cost'] # reduce energy by the cost of the move used
    
    def get_base_damage(self, move):
        return self.get_stat('attack') * ATTACK_DATA[move]['amount'] # base damage calculation for a move having factored in level from get_stat

    def gain_xp(self, amount):
        if self.level_up_xp > self.xp + amount: # amount of xp gained doesn't exceed level up threshold
            self.xp += amount
        else: # level up
            self.level += 1
            self.xp = (self.xp + amount) - self.level_up_xp # carry over excess XP to the next level
            self.level_up_xp = self.level * 150 # recalculate XP needed for next level

    def update(self, dt):
        if not self.paused:
            self.readiness += self.get_stat('speed') * dt # increase readiness based on speed stat and time elapsed