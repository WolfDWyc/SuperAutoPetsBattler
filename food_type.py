import json
import logging
from battler.get_targets import get_targets

COST = 3

class FoodType:
    """Represents a food type from Super Auto Pets"""

    def __init__(self, food_json: dict | str):
        """Initializes a food type from a JSON dictionary (or string) representing it."""
        if isinstance(food_json, str):
            food_json = json.loads(food_json)
        self.name = food_json['name']
        self.id = food_json['id']
        self.tier = food_json['tier']
        self.image_data = food_json['image']
        self.packs = food_json['packs']
        self.ability = food_json['ability']
        self.cost = food_json.get('cost', COST)
        if "probabilities" in food_json:
            self._init_probabilities(food_json)

        
    def _init_probabilities(self, pet_json):
        """Initializes the probabilities of the food type."""
        self.probabilities = {}
        for probability_json in pet_json["probabilities"]:
            if probability_json["kind"] == "shop":
                turn = int(probability_json["turn"].split("-")[1])
                self.probabilities[turn] = probability_json["perSlot"]
    
    def __str__(self):
        """Returns a string representation of the food type."""
        return self.name


    def trigger_event(self, event_type, event_data):
        """Triggers an event for the pet."""
        # logging.debug(f"              {self} triggered {event_type} in {event_data['team']}")
        ability = self.ability
            
        if not ability:
            return

        pets = event_data.get("team_pets_snapshot")
        if pets is None: # When abilities are out of battle, snapshots are not needed
            pets = event_data["team"].pets
        ability_trigger = ability["trigger"]
        if event_type == ability_trigger:
            ability_effect = ability["effect"]
            self.perform_ability(ability_effect, event_data)

    def perform_ability(self, ability_effect, event_data):
        """Performs the ability of the pet."""
        # TODO: Return True if casted, otherwise false, in order to trigger CastsAbility trigger type
        match ability_effect["kind"]:
            case "ModifyStats":
                affected_pets = self.perform_modify_stats_ability(ability_effect, event_data)
            case "GainExperience":
                affected_pets = self.perform_gain_experience_ability(ability_effect, event_data)
            case "ApplyStatus":
                affected_pets = self.perform_apply_status_ability(ability_effect, event_data)
            case _:
                return

        for pet in affected_pets:
            pet.trigger_event("EatsShopFood", {"food": self, "pet": pet} | event_data)

    def perform_apply_status_ability(self, ability_effect, event_data):
        """Performs the apply status ability of the food."""
        status_id = ability_effect["status"]
        targets = get_targets(ability_effect, event_data)
        for target in targets:
            target.status = event_data["status_types"][status_id]
        return targets

    def perform_gain_experience_ability(self, ability_effect, event_data):
        """Performs the gain experience ability of the food."""
        experience_amount = ability_effect["amount"]
        targets = get_targets(ability_effect, event_data)
        for target in targets:
            target.add_experience(experience_amount, event_data["turn"])
        return targets

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
            target_pets = get_targets(ability_effect, event_data, team_pets=team.pets)
            for pet in target_pets:
                pet.buff(health_amount, attack_amount, until_end_of_battle)
        return []
