
from shop import Shop
from team import Team
from pet_type import PetType
from pet import Pet

import random
import logging

REROLL_WEIGHT = 3
BUY_WEIGHT = 8
SELL_WEIGHT = 1


class ShopTurn:
    """Represents a super auto pets turn you can buy shop items in it."""

    def __init__(self, team: Team, pet_types: dict[str, PetType], turn: int, pack):
        """Initializes the shop turn."""
        self.shop = Shop(pet_types, turn, pack, team.buffs)
        self.team = team

    def get_move_options(self):
        """Returns a list of options for the move."""
        options = []
        weights = []
        reroll_weight = REROLL_WEIGHT
        buy_weight = BUY_WEIGHT
        sell_weight = SELL_WEIGHT
        # if not self.shop.can_buy_pet():
        #     reroll_weight = 4
        #     sell_weight = 8

        if self.shop.can_buy_pet() and self.team.can_add_pet():
            for i in range(self.shop.get_pet_count()):
                options.append(("buy_pet", i))
                weights.append(buy_weight)

        for pet in self.team.pets:
            options.append(("sell_pet", pet))
            weights.append(sell_weight)
        
        if self.shop.can_reroll():
            options.append(("reroll",))
            weights.append(reroll_weight)


        return options, weights

    def play_move(self):
        """Plays a move in the turn."""
        logging.debug(self.shop.gold)

        options, weights = self.get_move_options()
        if len(options) == 0 or all(option[0] == "sell_pet" for option in options):
            return False
        
        move = random.choices(population=options, weights=weights, k=1)[0]

        match move:
            case ["reroll"]:
                self.shop.reroll()
                logging.debug("Rerolled shop.")
                return True
            case ["buy_pet", index]:
                new_pet = self.shop.buy_pet(index)
                self.team.add_pet(new_pet)
                logging.debug(f"Bought pet {new_pet}.")
                return True
            case ["sell_pet", pet]:
                self.team.remove_pet(pet)
                self.shop.add_gold(pet.level)
                logging.debug(f"Sold pet {pet}.")
                return True

        return False
        
    def play(self):
        """Plays a turn in the shop."""
        while self.play_move():
            pass

        
