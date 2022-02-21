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

    # Rework battle turn to not depend on game, possible GameMetadata/GameData/Metadata class?
    def __init__(self, team_1: Team, team_2: Team, game=None):
        self.team_1 = team_1.clone()
        self.team_2 = team_2.clone()
        self.original_teams = {self.team_1: team_1, self.team_2: team_2}
        self.game = game
        self.event_data = {"pet_types": self.game.pet_types, "food_types": self.game.food_types, "status_types": self.game.status_types,
                            "turn_type": "battle", "turn": self, "team_1": self.team_1, "team_2": self.team_2}


    def play(self, log=True) -> BattleResult:
        """Play the battle and return the result."""
        if log:
            team_strings = [str(self.team_1), str(self.team_2)]
            # logging.debug(concat_strings_horizontally(team_strings, "|"))

        self.queued_attacks = {self.team_1: [], self.team_2: []}

        team_1_data = {"team": self.team_1, "original_team": self.original_teams[self.team_1], "enemy_team": self.team_2} | self.event_data
        team_2_data = {"team": self.team_2, "original_team": self.original_teams[self.team_2], "enemy_team": self.team_1} | self.event_data
        self.trigger_event("StartOfBattle", team_1_data | self.event_data)
        self.trigger_event("StartOfBattle", team_2_data | self.event_data)

        while True:
            if len(self.team_1.pets) == 0 and len(self.team_2.pets) == 0:
                battle_result = BattleResult.DRAW
                break
            elif len(self.team_1.pets) == 0:
                battle_result = BattleResult.TEAM_2_WIN
                break
            elif len(self.team_2.pets) == 0:
                battle_result = BattleResult.TEAM_1_WIN
                break

            self.play_next_attack()

            if log:
                team_strings = [str(self.team_1), str(self.team_2)]
                # logging.debug(concat_strings_horizontally(team_strings, "|"))

        for original_team in self.original_teams.values():
            for pet in original_team.pets:
                pet.trigger_end_of_battle()
        return battle_result

    def play_next_attack(self):
        team_1_pet = self.team_1.pets[-1]
        team_2_pet = self.team_2.pets[-1]

        self.play_attack(
            Attack(team_1_pet, self.team_1, [team_2_pet], team_1_pet.attack),
            Attack(team_2_pet, self.team_2, [team_1_pet], team_2_pet.attack)
        )

        while self.queued_attacks[self.team_1] or self.queued_attacks[self.team_2]:
            if self.queued_attacks[self.team_1]:
                attack = self.queued_attacks[self.team_1].pop(0)
                self.play_attack(attack, None)
            if self.queued_attacks[self.team_2]:
                attack = self.queued_attacks[self.team_2].pop(0)
                self.play_attack(None, attack)

    def queue_attack(self, attack, play_now=False):
        """Queue an attack."""
        team = attack.attacker_team
        if play_now:
            if team == self.team_1:
                self.play_attack(attack, None)
            else:
                self.play_attack(None, attack)
        else:
            self.queued_attacks[team].append(attack)

    def get_pet_team(self, pet):
        """Return the team that the pet belongs to."""
        if pet in self.team_1.pets:
            return self.team_1
        else:
            return self.team_2

    def play_attack(self, team_1_attack: Attack, team_2_attack: Attack):
        """Play a double-sided or single-sided attack"""
        team_1_data = {"team": self.team_1, "original_team": self.original_teams[self.team_1], "team_pets_snapshot": self.team_1.pets[:], "enemy_team": self.team_2} | self.event_data
        team_2_data = {"team": self.team_2, "original_team": self.original_teams[self.team_2], "team_pets_snapshot": self.team_2.pets[:], "enemy_team": self.team_1} | self.event_data
        team_data_dicts = {self.team_1: team_1_data, self.team_2: team_2_data}

        # Before the attack
        skip_attack = False
        if team_1_attack and team_1_attack.is_main_attack:
            self.trigger_event("BeforeAttack", {"pet": team_1_attack.attacker} | team_1_data, team_1_attack.is_main_attack)
            if all(target.health <= 0 for target in team_1_attack.targets):
                skip_attack = True

        if team_2_attack and team_2_attack.is_main_attack:
            self.trigger_event("BeforeAttack", {"pet": team_2_attack.attacker} | team_2_data, team_2_attack.is_main_attack)
            if all(target.health <= 0 for target in team_2_attack.targets):
                skip_attack = True

        # If a BeforeAttack ability killed all targets, skip the attack
        if skip_attack:
            return

        # Get attack targets
        team_1_targets = []
        team_2_targets = []
        if team_1_attack:
            team_1_targets = team_1_attack.targets
        if team_2_attack:
            team_2_targets = team_2_attack.targets
        if len(team_1_targets) != len(team_2_targets):
            most_targets = max(len(team_1_targets), len(team_2_targets))
            least_targets_list = min((team_1_targets, team_2_targets), key=len)
            least_targets_list += [None] * (most_targets - len(least_targets_list))

        # Play the attack
        for team_1_target, team_2_target in zip(team_1_targets, team_2_targets):
            cast_team_1_attack = (team_1_target and (team_1_target in self.team_1.pets or team_1_target in self.team_2.pets))
            cast_team_2_attack = (team_2_target and (team_2_target in self.team_1.pets or team_2_target in self.team_2.pets))
            team_1_target_team = team_1_target.team if cast_team_1_attack else None
            team_2_target_team = team_2_target.team if cast_team_2_attack else None

            if cast_team_1_attack:
                team_1_attack_damage = team_1_attack.attacker.attack_pet(team_1_target, team_1_attack.damage, team_1_attack.is_main_attack)
            if cast_team_2_attack:
                team_2_attack_damage = team_2_attack.attacker.attack_pet(team_2_target, team_2_attack.damage, team_2_attack.is_main_attack)
                
            if cast_team_1_attack and team_1_attack_damage:
                if team_1_target.health <= 0:
                    event_type = "Faint"
                else:
                    event_type = "Hurt"
                self.trigger_event(event_type, {"pet": team_1_target} | team_data_dicts[team_1_target_team])

            if cast_team_2_attack and team_2_attack_damage:
                if team_2_target.health <= 0:
                    event_type = "Faint"
                else:
                    event_type = "Hurt"
                self.trigger_event(event_type, {"pet": team_2_target} | team_data_dicts[team_2_target_team])

            if cast_team_1_attack and team_1_target.health <= 0:
                team_1_target_team.pets.remove(team_1_target)
                self.trigger_event("KnockOut", {"pet": team_1_attack.attacker} | team_1_data, team_1_attack.is_main_attack)
            if cast_team_2_attack and team_2_target.health <= 0:
                team_2_target_team.pets.remove(team_2_target)
                self.trigger_event("KnockOut", {"pet": team_2_attack.attacker} | team_2_data, team_2_attack.is_main_attack)

        # After the attack
        if team_1_attack and team_1_attack.is_main_attack:
            self.trigger_event("AfterAttack", {"pet": team_1_attack.attacker} | team_1_data, team_1_attack.is_main_attack)
        if team_2_attack and team_2_attack.is_main_attack:
            self.trigger_event("AfterAttack", {"pet": team_2_attack.attacker} | team_2_data, team_2_attack.is_main_attack)

    def trigger_event(self, event_type, event_data, include_self=True):
        """
        Called when a pet in the team triggers an event.
        """
        triggering_pet = event_data.get("pet")
        team = event_data["team"]
        for pet in team.pets:
            if not include_self and pet and pet == triggering_pet:
                continue
            if (pet.pet_type.id in self.game.triggers[event_type] or
                    (pet.status and pet.status.id in self.game.triggers[event_type])):
                pet.trigger_event(event_type, event_data)


    def enemy_team(self, team):
        """Return the other team."""
        if team == self.team_1:
            return self.team_2
        else:
            return self.team_1


