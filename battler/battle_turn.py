from enum import Enum

from team import Team
from pet_type import PetType
from pet import Pet
from battler.attack import Attack
import logging
from utils.concat import concat_strings_horizontally

class BattleResult(Enum):
    """Represents the result of a battle between 2 teams."""

    TEAM_1_WIN = 1
    TEAM_2_WIN = 2
    DRAW = 3

class BattleTurn:
    """Represents a super auto pets turn of a battle between 2 teams."""


    def __init__(self, team_1: Team, team_2: Team, game=None):
        self.team_1 = team_1.clone()
        self.team_2 = team_2.clone()
        self.original_teams = {self.team_1: team_1, self.team_2: team_2}
        self.game = game

    def play(self, log=True) -> BattleResult:
        """Play the battle and return the result."""
        if log:
            team_strings = [str(self.team_1), str(self.team_2)]
            logging.debug(concat_strings_horizontally(team_strings, "|"))

        self.queued_attacks = {self.team_1: [], self.team_2: []}
        while True:
            if len(self.team_1.pets) == 0 and len(self.team_2.pets) == 0:
                return BattleResult.DRAW
            elif len(self.team_1.pets) == 0:
                return BattleResult.TEAM_2_WIN
            elif len(self.team_2.pets) == 0:
                return BattleResult.TEAM_1_WIN

            self.play_next_attack()

            if log:
                team_strings = [str(self.team_1), str(self.team_2)]
                logging.debug(concat_strings_horizontally(team_strings, "|"))


    def play_next_attack(self):
        team_1_pet = self.team_1.pets[-1]
        team_2_pet = self.team_2.pets[-1]
        self.queue_attack(self.team_1, Attack(team_1_pet, [team_2_pet], team_1_pet.attack))
        self.queue_attack(self.team_2, Attack(team_2_pet, [team_1_pet], team_2_pet.attack))

        while self.queued_attacks[self.team_1] or self.queued_attacks[self.team_2]:
            if self.queued_attacks[self.team_1]:
                attack: Attack = self.queued_attacks[self.team_1].pop(0)
                self.play_attack(self.team_1, attack)
            logging.debug("")
            if self.queued_attacks[self.team_2]:
                attack: Attack = self.queued_attacks[self.team_2].pop(0)
                self.play_attack(self.team_2, attack)

    def queue_attack(self, team, attack, play_now=False):
        """Queue an attack."""
        if play_now:
            self.play_attack(team, attack)
        else:
            self.queued_attacks[team].append(attack)

    def play_attack(self, team, attack):
        """Play an attack on the enemy team."""
        event_data = {"pet_types": self.game.pet_types, "turn_type": "battle", "turn": self}
        enemy_team = self.enemy_team(team)
        team_data = {"team": team, "original_team": self.original_teams[team], "enemy_team": enemy_team} | event_data
        trigger_own_events = attack.trigger_own_events

        self.trigger_event("BeforeAttack", {"pet": attack.attacker} | team_data, trigger_own_events)
        # If BeforeAttack ability killed all targets, skip the attack
        if all(target.health <= 0 for target in attack.targets):
            return

        for target in attack.targets:
            if target not in team.pets and target not in enemy_team.pets:
                continue
            if target in team.pets:
                target_team = team
                target_team_data = {"team": target_team, "original_team": self.original_teams[target_team], "enemy_team": enemy_team} | event_data
            elif target in enemy_team.pets: # Redundant elif instead of else, but more readable
                target_team = enemy_team
                target_team_data = {"team": target_team, "original_team": self.original_teams[target_team], "enemy_team": team} | event_data

            target.health -= attack.damage
            if target.health <= 0:
                self.trigger_event("Faint", {"pet": target} | target_team_data, trigger_own_events)

                target_team.pets.remove(target)
                self.trigger_event("Knockout", {"pet": attack.attacker} | team_data, trigger_own_events)
            else:
                self.trigger_event("Hurt", {"pet": target} | target_team_data)
        self.trigger_event("AfterAttack", {"pet": attack.attacker} | team_data, trigger_own_events)

    def trigger_event(self, event_type, event_data, trigger_own_events=True):
        """Called when a pet in the team triggers an event."""
        triggering_pet = event_data["pet"]
        team = event_data["team"]
        for pet in team.pets:
            if not trigger_own_events and pet == triggering_pet:
                continue
            pet.trigger_event(event_type, event_data)

    def enemy_team(self, team):
        """Return the other team."""
        if team == self.team_1:
            return self.team_2
        else:
            return self.team_1


