from __future__ import annotations
import logging
from pet_type import PetType
from battler.get_targets import get_targets
import random

MAX_HEALTH = 50
MAX_ATTACK = 50

LEVEL_TO_EXPERIENCE = {
    1: 0,
    2: 2,
    3: 5,
}

EXPERIENCE_TO_LEVEL = {
    0: 1,
    1: 1,
    2: 2,
    3: 2,
    4: 2,
    5: 3,
}

class Pet:
    """Represents a playable pet in super auto pets."""
    def __init__(self, pet_type, team=None, health=-1, attack=-1, level=1, experience=-1, status=None, abilities=None):
        self.buffs = []
        self.state = {}
        self.pet_type = pet_type
        self.team = team
        if health == -1:
            health = self.pet_type.health
        self.health = health
        if attack == -1:
            attack = self.pet_type.attack
        self.attack = attack
        self.level = level
        self.experience = experience
        if experience == -1:
            self.experience = LEVEL_TO_EXPERIENCE[level]
        self.level = level
        self.status = status
        self.abilities = pet_type.abilities
        if abilities is not None:
            self.abilities = abilities

    def add_experience(self, experience_amount, shop_turn):
        """Adds experience to the pet."""
        if self.level == 3:
            return 0
        self.old_level = self.level
        for i in range(experience_amount):
            self.experience += 1
            self.buff(1, 1, False)
            new_level = EXPERIENCE_TO_LEVEL.get(self.experience, 3)
            if new_level > self.level:
                shop_turn.trigger_event("LevelUp", {"pet": self, "team": self.team, "original_team": self.team, "turn": shop_turn, "turn_type": "shop"})
                self.level = new_level
                if self.level == 3:
                    return i
        return experience_amount

    def attack_pet(self, target: Pet, attack_damage, is_main_attack=True):
        """Attacks the target."""
        damage_modifier = 0
        target_damage_modifier = 0
        if is_main_attack and self.status:
            status_ability = self.status.ability
            status_ability_effect = status_ability["effect"]
            if status_ability["trigger"] == "WhenAttacking" and status_ability_effect["kind"] == "ModifyDamage":
                damage_modifier = status_ability_effect.get("damageModifier")
                if status_ability_effect["appliesOnce"]:
                    self.status = None
        if target.status:
            status_ability = target.status.ability
            status_ability_effect = status_ability["effect"]
            if status_ability["trigger"] == "WhenDamaged" and status_ability_effect["kind"] == "ModifyDamage":
                target_damage_modifier = status_ability_effect.get("damageModifier")
                if status_ability_effect["appliesOnce"]:
                    target.status = None

        if damage_modifier != 0:
            if damage_modifier is None:
                attack_damage = None
            else:
                attack_damage += damage_modifier
        if target_damage_modifier != 0:
            if target_damage_modifier is None: 
                attack_damage = 0
            elif target_damage_modifier == 20 and damage_modifier is None: # Melon armor edge case
                attack_damage = 0
            else:
                attack_damage -= target_damage_modifier

        health_before = target.health
        if attack_damage is None:
            target.health = 0
        else:
            target.health -= attack_damage

        return health_before - target.health

    def __str__(self) -> str:
        """Returns a string representation of the pet."""
        pet_info = f"L{self.level}.{self.experience} {self.pet_type.name} [{self.attack}⚔|{self.health}❤]"
        if self.status:
            pet_info += f" w/{self.status}"
        return pet_info
         

    def clone(self):
        """Returns a clone of the pet."""
        return Pet(self.pet_type, self.team, self.health, self.attack, self.level, self.experience, self.status, self.abilities)

    def get_ability(self):
        """Returns the ability of the pet."""
        if self.abilities and self.abilities.get(self.level):
            return self.abilities[self.level]
        return None

    def get_state(self):
        """Gets the state of the pet. A state persists until end of battle."""
        return self.state

    def set_state(self, state):
        """Sets the state of the pet. A state persists until end of battle."""
        self.state = state

    def trigger_end_of_battle(self):
        # Remove temporary buffs (given when until_end_of_battle is true)
        for buff in self.buffs:
            health, attack = buff
            self.health -= health
            self.attack -= attack
        self.buffs = []
        self.state = {}

    def buff(self, health_amount, attack_amount, until_end_of_battle=False):
        """Adds attack to the pet."""
        self.health += health_amount
        self.health = min(self.health, MAX_HEALTH)

        self.attack += attack_amount
        self.attack = min(self.attack, MAX_ATTACK)
        
        if until_end_of_battle:
            self.buffs.append((health_amount, attack_amount))

    def trigger_event(self, event_type, event_data):
        """Triggers an event for the pet."""
        abilities = []
        if self.get_ability():
            abilities.append(self.get_ability())
        if self.status:
            abilities.append(self.status.ability)
        for ability in abilities:
            # logging.debug(f"              {self} triggered by {event_type} of {event_data.get('pet')} in {event_data['team']}")
            
            pets = event_data.get("team_pets_snapshot")
            if pets is None: # When abilities are out of battle, snapshots are not needed
                pets = event_data["team"].pets
            ability_trigger = ability["trigger"]
            ability_trigger_kind = ability["triggeredBy"]["kind"]
            if ((event_type == ability_trigger) and 
                    ((ability_trigger_kind == "Player")
                    or (ability_trigger_kind == "Self" and self == event_data["pet"]) 
                    or (ability_trigger_kind == "EachFriend" and self != event_data["pet"])
                    or (ability_trigger_kind == "FriendAhead" and self == pets[pets.index(event_data["pet"]) - 1]))):
                ability_effect = ability["effect"]
                self.perform_ability(ability_effect, event_data)

    def perform_ability(self, ability_effect, event_data):
        """Performs the ability of the pet."""
        # TODO: Return True if casted, otherwise false, in order to trigger CastsAbility trigger type
        match ability_effect["kind"]:
            case "OneOf":
                effect = random.choice(ability_effect["effects"])
                self.perform_ability(effect, event_data)
            case "AllOf":
                for effect in ability_effect["effects"]:
                    self.perform_ability(effect, event_data)
            case "ModifyStats":
                self.perform_modify_stats_ability(ability_effect, event_data)
            case "SummonPet":
                self.perform_summon_pet_ability(ability_effect, event_data)
            case "SummonRandomPet": 
                self.perform_summon_random_pet_ability(ability_effect, event_data)
            case "RespawnPet":
                self.perform_respawn_pet_ability(ability_effect, event_data)
            case "GainGold":
                self.perform_gain_gold_ability(ability_effect, event_data)
            case "DealDamage":
                self.perform_deal_damage_ability(ability_effect, event_data, self.get_ability()["trigger"])
            case "TransferStats":
                self.perform_transfer_stats_ability(ability_effect, event_data)
            case "ReduceHealth":
                self.perform_reduce_health_ability(ability_effect, event_data)
            case "Evolve":
                self.perform_evolve_ability(ability_effect, event_data)
            case "GainExperience":
                self.perform_gain_experience_ability(ability_effect, event_data)
            case "ApplyStatus":
                self.perform_apply_status_ability(ability_effect, event_data)
            case "SplashDamage":
                self.perform_splash_damage_ability(ability_effect, event_data)
            case "TransferAbility":
                self.perform_transfer_ability_ability(ability_effect, event_data)
            case "RepeatAbility":
                self.perform_repeat_ability_ability(ability_effect, event_data)
            case _:
                return

        if (event_data["turn_type"] == "battle" and not event_data.get("repeated") and ability_effect["kind"] != "RepeatAbility"
            and self.get_ability()["effect"] == ability_effect):
            cloned_event_data = event_data.copy()
            cloned_event_data["pet"] = self
            event_data["turn"].trigger_event("CastsAbility", {"ability_event_data": event_data | {"repeated": True}} | cloned_event_data)


    def perform_repeat_ability_ability(self, ability_effect, event_data):
        """Performs the repeat ability ability of the pet."""
        targets = get_targets(ability_effect, event_data, pet=self, team_pets=self.team.pets)
        for target in targets:
            target.perform_ability(event_data["pet"].get_ability()["effect"], event_data["ability_event_data"])


    def perform_transfer_ability_ability(self, ability_effect, event_data):
        """Performs the transfer ability ability of the pet."""
        team =  self.team

        ability_from = ability_effect["from"]
        pet_from = None
        pets_to = []
        match ability_from["kind"]:
            case "FriendAhead":
                if self != team.pets[-1]:
                    pet_from = team.pets[team.pets.index(self) + 1]
        targets = get_targets(ability_effect, event_data, pet=self, team_pets=self.team.pets)

        if pet_from and targets:       
            for pet_to in pets_to:
                pet_to.abilities = pet_from.abilities  

    def perform_splash_damage_ability(self, ability_effect, event_data):
        """Performs the splash damage ability of the pet."""
        enemy_team = event_data["enemy_team"]
        damage = ability_effect["amount"]

        from battler.battle_turn import BattleTurn
        from battler.attack import Attack

        turn: BattleTurn = event_data["turn"]

        if len(enemy_team.pets) > 1:
            target = enemy_team.pets[-2]
            turn.queue_attack(Attack(self, self.team, [target], damage, False), False)
    

    def perform_apply_status_ability(self, ability_effect, event_data):
        """Performs the apply status ability of the food."""
        status_id = ability_effect["status"]
        targets = get_targets(ability_effect, event_data, pet=self, team_pets=self.team.pets, enemy_pets=event_data["enemy_team"].pets)
        for target in targets:
            target.status = event_data["status_types"][status_id]
        return targets

    def perform_gain_experience_ability(self, ability_effect, event_data):
        """Performs the gain experience ability of the pet."""
        experience_amount = ability_effect["amount"]
        targets = get_targets(ability_effect, event_data, pet=self, team_pets=self.team)
        for target in targets:
            target.add_experience(experience_amount, event_data["turn"])


    def perform_evolve_ability(self, ability_effect, event_data):
        """Performs an evolve ability."""
        team = self.team
        evolve_into_id = ability_effect["into"]
        evovle_into_pet_type = event_data["pet_types"][evolve_into_id]
        team.remove_pet(self)
        team.add_pet(Pet(evovle_into_pet_type, team))

    def perform_reduce_health_ability(self, ability_effect, event_data):
        """Performs a reduce health ability."""
        percentage = ability_effect["percentage"]
        targets = get_targets(ability_effect, event_data, enemy_pets=event_data["enemy_team"].pets)
        from battler.attack import Attack
        from battler.battle_turn import BattleTurn
        turn: BattleTurn = event_data["turn"]

        for target in targets:
            damage_amount = min(int(target.health * percentage), target.health - 1) # Reduce health can't currently kill
            # TODO: Test this
            target.health -= damage_amount

    def perform_transfer_stats_ability(self, ability_effect, event_data):
        """Performs the transfer stats ability of the pet."""
        team = self.team

        ability_from = ability_effect["from"]
        pet_from = None
        pets_to = []
        match ability_from["kind"]:
            case "FriendAhead":
                if self != team.pets[-1]:
                    pet_from = team.pets[team.pets.index(self) + 1]
            case "StrongestFriend":
                team_clone = team.clone()
                if self in team_clone.pets:
                    team_clone.pets.remove(self)
                pet_from = max(team_clone.pets, key=lambda pet: pet.health + pet.attack)
            case "Self":
                pet_from = self


        targets = get_targets(ability_effect, event_data, pet=self, team_pets=team.pets)

        if pet_from and targets:       
            for pet_to in pets_to:
                if ability_effect["copyHealth"]:
                    pet_to.health = pet_from.health
                if ability_effect["copyAttack"]:
                    pet_to.attack = pet_from.attack

    def perform_modify_stats_ability(self, ability_effect, event_data):
        """Performs the modify stats ability of the pet."""
        health_amount = ability_effect.get("healthAmount", 0)
        attack_amount = ability_effect.get("attackAmount", 0)
        ability_target = ability_effect["target"]

        until_end_of_battle = False
        if event_data["turn_type"] == "shop":
            team = event_data["original_team"]
            until_end_of_battle = ability_effect["untilEndOfBattle"]
        elif event_data["turn_type"] == "battle":
            team = event_data["team"]

        if ability_target["kind"] == "EachShopAnimal":
            if ability_target["includingFuture"]:
                shop = event_data["shop"]
                shop.buff_shop(health_amount, attack_amount)
        else:
            target_pets = get_targets(ability_effect, event_data, pet=self, team_pets=team.pets)
            for pet in target_pets:
                pet.buff(health_amount, attack_amount, until_end_of_battle)

    def perform_summon_random_pet_ability(self, ability_effect, event_data):
        """Performs a summon random pet ability."""
        pet_types = event_data["pet_types"]
        cloned_event_data = event_data.copy()

        tier = ability_effect["tier"]
        health_amount = ability_effect.get("baseHealth", -1) 
        attack_amount = ability_effect.get("baseAttack", -1)
        level = ability_effect.get("level", 1)

        pet_types_in_tier = PetType.by_tier(pet_types, tier)
        pet_type = random.choice(pet_types_in_tier)
        pet = Pet(pet_type, self.team, health_amount, attack_amount, level)
        cloned_event_data["pet"] = pet
        event_data["team"].add_pet(pet)
        event_data["turn"].trigger_event("Summoned", cloned_event_data)
    
    def perform_summon_pet_ability(self, ability_effect, event_data):
        """Performs a summon pet ability."""
        pet_types = event_data["pet_types"]

        health_amount = ability_effect.get("withHealth", -1)
        attack_amount = ability_effect.get("withAttack", -1)
        summoned_pet_type = pet_types[ability_effect["pet"]]
        turn = event_data["turn"]

        # TODO: Summon pet in-place of the triggering pet, and not at the front of the team
        match ability_effect["team"]:
            case "Friendly":
                cloned_event_data = event_data.copy()
                pet = Pet(summoned_pet_type, self.team, health_amount, attack_amount)
                cloned_event_data["pet"] = pet

                # EDGE CASE: MISSING INFORMATION [SHEEP]
                if self.pet_type.id == "pet-sheep":
                    event_data["team"].add_pet(pet)

                    pet_clone = pet.clone()
                    event_data["team"].add_pet(pet_clone)
                    cloned_event_data_clone = cloned_event_data.copy()
                    cloned_event_data_clone["pet"] = pet_clone
                    turn.trigger_event("Summoned", cloned_event_data_clone)
                # EDGE CASE: MISSING INFORMATION [ROOSTER]
                elif pet.pet_type.id == "pet-chick":
                    pet.attack = self.attack
                    event_data["team"].add_pet(pet)
                # EDGE CASE: MISSING INFORMATION [FLY]
                elif pet.pet_type.id == "pet-zombie-fly":
                    if event_data["pet"].pet_type.id != "pet-zombie-fly":
                        event_data["team"].add_pet(pet)
                else:    
                    event_data["team"].add_pet(pet)
                turn.trigger_event("Summoned", cloned_event_data)

            case "Enemy":
                cloned_event_data = event_data.copy()
                pet = Pet(summoned_pet_type, cloned_event_data["enemy_team"], health_amount, attack_amount)
                cloned_event_data["pet"] = pet

                cloned_event_data["team"], cloned_event_data["enemy_team"] = cloned_event_data["enemy_team"], cloned_event_data["team"]
                if cloned_event_data["original_team"] == cloned_event_data["enemy_team"]:  
                    cloned_event_data["original_team"] = cloned_event_data["team"]
                else:
                    cloned_event_data.pop("original_team")
                cloned_event_data.pop("team_pets_snapshot")

                # EDGE CASE: MISSING INFORMATION [RAT]
                if self.pet_type.id == "pet-rat":
                    event_data["enemy_team"].add_pet(pet, 0)
                else:
                    event_data["enemy_team"].add_pet(pet)
                turn.trigger_event("Summoned", cloned_event_data)


    def perform_respawn_pet_ability(self, ability_effect, event_data):
        turn = event_data["turn"]

        health_amount = ability_effect.get("baseAttack")
        attack_amount = ability_effect.get("baseHealth")
        summoned_pet_type = self.pet_type

        cloned_event_data = event_data.copy()
        pet = Pet(summoned_pet_type, self.team, health_amount, attack_amount, self.level)
        cloned_event_data["pet"] = pet

        event_data["team"].add_pet(pet)
        turn.trigger_event("Summoned", cloned_event_data)



    def perform_gain_gold_ability(self, ability_effect, event_data):
        """Performs the gain gold ability of the pet."""
        shop = event_data["shop"]
        gold_amount = ability_effect["amount"]
        shop.gold += gold_amount

    def perform_deal_damage_ability(self, ability_effect, event_data, ability_trigger):
        """Performs the deal damage ability of the pet."""
        from battler.attack import Attack

        # TODO: Currently ignoring attacking while in a shop turn (using sleeping pills).
        if event_data["turn_type"] == "battle":
            deal_damage_now = ability_trigger == "BeforeAttack" or ability_trigger == "StartOfBattle"
            team = self.team
            pets = team.pets
            enemy_pets = event_data["enemy_team"].pets

            from battler.battle_turn import BattleTurn
            turn: BattleTurn = event_data["turn"]

            if "amount" in ability_effect:
                damage_amount = ability_effect["amount"]
            elif "attackDamagePercent" in ability_effect:
                damage_amount = int(self.attack * ability_effect["attackDamagePercent"]/100)
            
            targets = get_targets(ability_effect, event_data, pet=self, team_pets=pets, enemy_pets=enemy_pets)
            turn.queue_attack(Attack(self, team, targets, damage_amount, False), deal_damage_now)
                        


