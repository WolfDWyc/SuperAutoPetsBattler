import logging
from pet_type import PetType
import random

MAX_HEALTH = 50
MAX_ATTACK = 50

class Pet:
    """Represents a playable pet in super auto pets."""

    def __init__(self, pet_type, health=-1, attack=-1, level=-1):
        self.pet_type = pet_type
        if health == -1:
            health = self.pet_type.health
        self.health = health
        if attack == -1:
            attack = self.pet_type.attack
        self.attack = attack
        if level == -1:
            level = 1
        self.level = level

    def __str__(self) -> str:
        """Returns a string representation of the pet."""
        return f"{self.pet_type.name} [{self.attack}⚔|{self.health}❤]"

    def clone(self):
        """Returns a clone of the pet."""
        return Pet(self.pet_type, self.health, self.attack, self.level)

    def get_ability(self):
        """Returns the ability of the pet."""
        if self.pet_type.abilities and self.pet_type.abilities.get(self.level):
            return self.pet_type.abilities[self.level]
        return None

    def trigger_event(self, event_type, event_data):
        """Triggers an event for the pet."""
        logging.debug(f"              {self} triggered by {event_type} of {event_data['pet']} in {event_data['team']}")
        ability = self.get_ability()
        if not ability:
            return
        ability_trigger = ability["trigger"]
        ability_trigger_kind = ability["triggeredBy"]["kind"]
        if ((event_type == ability_trigger) and 
                ((ability_trigger_kind == "Self" and self == event_data["pet"]) 
                or (ability_trigger_kind == "EachFriend" and self != event_data["pet"])
                or (ability_trigger_kind == "FriendAhead" and self == event_data["team"].pets[event_data["team"].pets.index(event_data["pet"]) - 1])
                or (ability_trigger_kind  == "Player"))):
            ability_effect = ability["effect"]
            match ability_effect["kind"]:
                case "OneOf":
                    effect = random.choice(ability_effect["effects"])
                    self.perform_ability(effect, event_data)
                case "AllOf":
                    for effect in ability_effect["effects"]:
                        self.perform_ability(effect, event_data)
                case _:
                    self.perform_ability(ability_effect, event_data)

    def add_health(self, amount):
        """Adds health to the pet."""
        self.health += amount
        self.health = min(self.health, MAX_HEALTH)

    def add_attack(self, amount):
        """Adds attack to the pet."""
        self.attack += amount
        self.attack = min(self.attack, MAX_ATTACK)

    def perform_ability(self, ability_effect, event_data):
        """Performs the faint ability of the pet."""
        match ability_effect["kind"]:
            case "ModifyStats":
                self.perform_modify_stats_ability(ability_effect, event_data)
            case "SummonPet":
                self.perform_summon_pet_ability(ability_effect, event_data)
            case "SummonRandomPet": 
                self.perform_summon_random_pet_ability(ability_effect, event_data)
            case "GainGold":
                self.perform_gain_gold_ability(ability_effect, event_data)
            case "DealDamage":
                self.perform_deal_damage_ability(ability_effect, event_data, self.get_ability()["trigger"])

    def perform_modify_stats_ability(self, ability_effect, event_data):
        """Performs a modify stats ability."""
        health_amount = ability_effect.get("healthAmount", 0)
        attack_amount = ability_effect.get("attackAmount", 0)
        ability_target = ability_effect["target"]

        # TODO: Impelment untilEndOfBattle
        if event_data["turn_type"] == "shop":
            team = event_data["original_team"]
        elif event_data["turn_type"] == "battle":
            team = event_data["team"]
        match ability_target["kind"]:
            case "Self":
                if self == event_data["pet"]:
                    self.add_health(health_amount)
                    self.add_attack(attack_amount)
            case "TriggeringEntity":
                pet = event_data["pet"]
                pet.add_health(health_amount)
                pet.add_attack(attack_amount)
            case "RandomFriend":
                pets = team.pets[:]
                if self in pets:
                    pets.remove(self)
                affected_pets = random.sample(pets, min(ability_target["n"], len(pets)))
                for pet in affected_pets:
                    pet.add_health(health_amount)
                    pet.add_attack(attack_amount)
            case "EachFriend":
                pets = team.pets[:]
                if self in pets:
                    pets.remove(self)
                for pet in team.pets:
                    pet.add_health(health_amount)
                    pet.add_attack(attack_amount)
            case "Level2And3Friends":
                pets = team.pets[:]
                if self in pets:
                    pets.remove(self)
                for pet in team.pets:
                    if pet.level == 2 or pet.level == 3:
                        pet.add_health(health_amount)
                        pet.add_attack(attack_amount)
            case "DifferentTierAnimals":
                tiers = set()
                for pet in team.pets:
                    if pet.pet_type.tier not in tiers:
                        tiers.add(pet.pet_type.tier)
                        pet.add_health(health_amount)
                        pet.add_attack(attack_amount)
            case "AdjacentFriends":
                pets = team.pets
                index = pets.index(event_data["pet"])
                for pet_index in [index - 1, index + 1]:
                    if 0 <= index < len(pets):
                        pet = pets[pet_index]
                        pet.add_health(health_amount)
                        pet.add_attack(attack_amount) 
            case "LeftMostFriend":
                pets = team.pets
                if len(pets) > 0:
                    pet = pets[0]
                    pet.add_health(health_amount)
                    pet.add_attack(attack_amount)
            case "RightMostFriend":
                pets = team.pets
                if len(pets) > 0:
                    pet = pets[-1]
                    pet.add_health(health_amount)
                    pet.add_attack(attack_amount)
            case "FriendBehind":
                pets = team.pets
                pet_amount = ability_target["n"]
                index = pets.index(event_data["pet"]) - 1
                for pet_index in range(index, index - pet_amount, -1):
                    if 0 <= index < len(pets):
                        pet = pets[pet_index]
                        pet.add_health(health_amount)
                        pet.add_attack(attack_amount) 
            case "FriendAhead":
                pets = team.pets
                pet_amount = ability_target["n"]
                index = pets.index(event_data["pet"]) + 1
                for pet_index in range(index + 1, index + pet_amount):
                    if 0 <= index < len(pets):
                        pet = pets[pet_index]
                        pet.add_health(health_amount)
                        pet.add_attack(attack_amount)
            case "EachShopAnimal":
                if ability_target["includingFuture"]:
                    shop = event_data["shop"]
                    shop.buff_shop(health_amount, attack_amount)
                else:
                    team = event_data["team"]
                    team.add_buff(health_amount, attack_amount)

    def perform_summon_random_pet_ability(self, ability_effect, event_data):
        """Performs a summon random pet ability."""
        pet_types = event_data["pet_types"]

        tier = ability_effect["tier"]
        health_amount = ability_effect.get("baseAealth", -1) 
        attack_amount = ability_effect.get("baseAttack", -1)
        level = ability_effect.get("level", -1)

        pet_types_in_tier = PetType.by_tier(pet_types, tier)
        pet_type = random.choice(pet_types_in_tier)
        pet = Pet(pet_type, health_amount, attack_amount, level)
        event_data["team"].add_pet(pet)

    def perform_summon_pet_ability(self, ability_effect, event_data):
        """Performs a summon pet ability."""
        pet_types = event_data["pet_types"]

        health_amount = ability_effect.get("withHealth", -1)
        attack_amount = ability_effect.get("withAttack", -1)
        summoned_pet_type = pet_types[ability_effect["pet"]]

        pet = Pet(summoned_pet_type, health_amount, attack_amount)
        match ability_effect["team"]:
            case "Friendly":
                # EDGE CASE: MISSING INFORMATION [SHEEP]
                if self.pet_type.id == "pet-sheep":
                    event_data["team"].add_pet(pet)
                    event_data["team"].add_pet(pet.clone())
                # EDGE CASE: MISSING INFORMATION [DEER]
                elif self.pet_type.id == "pet-deer":
                    event_data["team"].add_pet(pet)
                    # TODO: Give Splash Attack (FOOD W.I.P)
                # EDGE CASE: MISSING INFORMATION [ROOSTER]
                elif self.pet_type.id == "pet-rooster":
                    pet.attack = self.attack
                    event_data["team"].add_pet(pet)
                else:    
                    event_data["team"].add_pet(pet)
            case "Enemy":
                # EDGE CASE: MISSING INFORMATION [RAT]
                if self.pet_type.id == "pet-rat":
                    event_data["enemy_team"].add_pet(pet, 0)
                else:
                    event_data["enemy_team"].add_pet(pet)

    def perform_gain_gold_ability(self, ability_effect, event_data):
        """Performs the gain gold ability of the pet."""
        shop = event_data["shop"]
        gold_amount = ability_effect["amount"]
        shop.gold += gold_amount

    def perform_deal_damage_ability(self, ability_effect, event_data, ability_trigger):
        """Performs the deal damage ability of the pet."""
        from battler.attack import Attack

        # Currently ignoring attacking while in a shop turn (using sleeping pills).
        if event_data["turn_type"] == "battle":
            deal_damage_now = ability_trigger == "BeforeAttack"
            ability_target = ability_effect["target"]
            team = event_data["team"]
            pets = team.pets
            enemy_pets = event_data["enemy_team"].pets

            from battler.battle_turn import BattleTurn
            turn: BattleTurn = event_data["turn"]

            if "amount" in ability_effect:
                damage_amount = ability_effect["amount"]
            elif "attackDamagePercent" in ability_effect:
                damage_amount = int(self.attack * ability_effect["attackDamagePercent"]/100)
            match ability_target["kind"]:
                case "All":
                    turn.queue_attack(team, Attack(self, enemy_pets + pets, damage_amount, False), deal_damage_now)
                case "EachEnemy":
                    turn.queue_attack(team, Attack(self, enemy_pets, damage_amount, False), deal_damage_now)
                case "RandomEnemy":
                    affected_pets = random.sample(enemy_pets, min(ability_target["n"], len(enemy_pets)))
                    turn.queue_attack(team, Attack(self, affected_pets, damage_amount, False), deal_damage_now)
                case "FirstEnemy":
                    if len(enemy_pets) > 0:
                        turn.queue_attack(team, Attack(self, [enemy_pets[-1]], damage_amount, False), deal_damage_now)
                case "LastEnemy":
                    if len(enemy_pets) > 0:
                        turn.queue_attack(team, Attack(self, [enemy_pets[0]], damage_amount, False), deal_damage_now)
                case "LowestHealthEnemy":
                    lowest_health_pet = min(enemy_pets, key=lambda pet: pet.health)
                    turn.queue_attack(team, Attack(self, [lowest_health_pet], damage_amount, False), deal_damage_now)
                case "FriendBehind":
                    index = pets.index(event_data["pet"])
                    if index != 0:
                        target_pet = pets[index - 1]
                        turn.queue_attack(team, Attack(self, [target_pet], damage_amount, False), deal_damage_now)
                case "AdjacentAnimals":
                    target_pets = []
                    if len(enemy_pets) > 0:
                        target_pets.append(enemy_pets[-1])
                    index = pets.index(event_data["pet"])
                    if index != 0:
                        target_pets.append(pets[index - 1])
                    turn.queued_attack(team, Attack(self, target_pets, damage_amount, False), deal_damage_now)
                        


