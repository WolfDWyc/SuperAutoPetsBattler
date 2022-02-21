
from food_type import FoodType
from shop import Shop
from battler.player import Player
from pet_type import PetType
from pet import Pet

import random
import logging

REROLL_WEIGHT = 2
BUY_PET_WEIGHT = 15
MERGE_PET_WEIGHT = 45
BUY_FOOD_WEIGHT = 6
SELL_PET_WEIGHT = 0.05

class ShopTurn:
    """Represents a super auto pets turn you can buy shop items in it."""
    # TODO: Rework to not depend on player and/or game
    def __init__(self, player: Player, game, team=None, shop=None):
        """Initializes the shop turn."""
        self.player = player
        self.game = game
        self.team = team
        self.shop = shop
        if team is None:
            self.team = self.player.team
        if shop is None:
            self.shop = Shop(self.game.pet_types, self.game.food_types, self.game.turn, self.game.pack, self.team.buffs)

        self.event_data = {"pet_types": self.game.pet_types, "food_types": self.game.food_types, "status_types": self.game.status_types,
                            "turn_type": "shop", "turn": self, "shop": self.shop, "team": self.team, "original_team": self.team}

    def get_move_options(self):
        """Returns a list of options for the move."""
        options = []
        weights = []
        reroll_weight = REROLL_WEIGHT
        buy_pet_weight = BUY_PET_WEIGHT
        merge_pet_weight = MERGE_PET_WEIGHT
        buy_food_weight = BUY_FOOD_WEIGHT
        sell_pet_weight = SELL_PET_WEIGHT
        # if not self.shop.can_buy_pet():
        #     reroll_weight = 4
        #     sell_weight = 8

        if self.shop.can_buy_pet() and self.team.can_add_pet():
            for pet_index in range(self.shop.get_pet_count()):
                for j in range(-1, self.team.TEAM_SIZE):
                    options.append(("buy_pet", pet_index, j, -1))
                    weights.append(buy_pet_weight)
                    if 0 <= j < len(self.team.pets) and self.team.pets[j].pet_type.id == self.shop.get_pets()[pet_index].pet_type.id:
                        options.append(("buy_pet", pet_index, j, j))
                        weights.append(merge_pet_weight)

        for food_index in range(self.shop.get_food_count()):
            if self.shop.can_buy_food(food_index):
                for j in range(len(self.team.pets)):
                    options.append(("buy_food", food_index, j))
                    weights.append(buy_food_weight)

        for pet_index in range(len(self.team.pets)):
            options.append(("sell_pet", pet_index))
            weights.append(sell_pet_weight)
        
        if self.shop.can_reroll():
            options.append(("reroll",))
            weights.append(reroll_weight)

        return options, weights

    def choose_move(self):
        """Choose a move."""
        
        options, weights = self.get_move_options()
        if not self.are_moves_left(options):
            return []

        return random.choices(population=options, weights=weights, k=1)[0]

    @staticmethod
    def are_moves_left(move_options):
        """Returns if there are moves left."""
        return len(move_options) != 0 and not all(option[0] == "sell_pet" for option in move_options)

    def play_move(self, move):
        """Plays a move in the turn."""
        ## logging.debug(self.shop.gold)

        match move:
            case ["reroll"]:
                self.shop.reroll()
                ## logging.debug("Rerolled shop.")
                return True
            case ["buy_pet", pet, team_index, merge]:
                return self.buy_pet(pet, team_index, merge)
            case ["sell_pet", pet]:
                return self.sell_pet(pet)
            case ["buy_food", food, team_index]:
                return self.buy_food(food, team_index)

        return False

    def buy_food(self, food: FoodType | int, team_index):
        """Buys food from the shop."""
        food = self.shop.buy_food(food)
        bought = food is not None
        if bought:
            # logging.debug(f"Bought food {food}.")
            food.trigger_event("BuyFood", {"food": food, "purchase_target": self.team.pets[team_index]} | self.event_data)

    def buy_pet(self, pet: Pet | int, buy_index, merge_index=-1):
        """Buys a pet from the shop."""
        if merge_index != -1 and not self.team.can_add_pet():
            return False
        new_pet = self.shop.buy_pet(pet)
        bought = new_pet is not None
        new_pet.team = self.team
        if bought:
            if merge_index == -1:
                # logging.debug(f"Bought pet {new_pet}.")
                self.team.add_pet(new_pet, buy_index)
            else: 
                merge_pet = self.team.pets[merge_index]
                # logging.debug(f"Merged pet {new_pet} to {merge_pet}.")
                merge_pet.add_experience(1, self)

            self.trigger_event("Buy", {"pet": new_pet} | self.event_data)
            if new_pet.pet_type.tier == 1:
                self.trigger_event("BuyTier1Animal", {"pet": new_pet} | self.event_data)
            if self.game.battle_results and self.player == self.game.battle_results[-1]["loser"]:
                self.trigger_event("BuyAfterLoss", {"pet": new_pet} | self.event_data)
            if merge_index == -1:
                self.trigger_event("Summoned", {"pet": new_pet} | self.event_data)
                

        return bought

    def sell_pet(self, pet: Pet | int):
        "Sells a pet."
        if isinstance(pet, int):
            pet = self.team.pets[pet]
        sell_result = self.team.remove_pet(pet)
        if sell_result:
            # logging.debug(f"Sold pet {pet}.")
            self.shop.add_gold(pet.level)
            self.trigger_event("Sell", {"pet": pet} | self.event_data)
        return sell_result
        
    def play(self):
        """Plays a turn in the shop."""
        self.trigger_event("StartOfTurn", self.event_data)
        while True:
            move = self.choose_move()
            if not move or not self.play_move(move):
                break
        self.end_turn()

    def end_turn(self):
        self.trigger_event("EndOfTurn", self.event_data)
        if self.shop.gold >= 3:
            self.trigger_event("EndOfTurnWith3PlusGold", self.event_data)
        if self.shop.gold >= 2:
            self.trigger_event("EndOfTurnWith2PlusGold", self.event_data)
        if len(self.team.pets) <= 4:
            self.trigger_event("EndOfTurnWith4OrLessAnimals", self.event_data)
        if any(pet.level == 3 for pet in self.team.pets):
            self.trigger_event("EndOfTurnWithLvl3Friend", self.event_data)


    def trigger_event(self, event_type, event_data, trigger_own_events=True):
        """Called when a pet in the team triggers an event."""
        triggering_pet = event_data.get("pet")
        triggering_food = event_data.get("food")
        team = event_data["team"]
        for pet in team.pets:
            if not trigger_own_events and pet and pet == triggering_pet:
                continue
            if (pet.pet_type.id in self.game.triggers[event_type] or
                (triggering_food and triggering_food.id in self.game.triggers[event_type])):
                pet.trigger_event(event_type, event_data)

        
    def clone(self):
        """Returns a clone of this shop turn."""
        return ShopTurn(self.player, self.game, self.team.clone(), self.shop.clone())
