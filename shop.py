import logging
import random
from food_type import FoodType

from pet_type import PetType
from pet import Pet

TURNS_TO_TIERS = {
    1: 1,
    2: 1,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
    7: 4,
    8: 4,
    9: 5,
    10: 5,
    11: 6, 
}

TIERS_TO_SIZE = {
    1: (3, 1),
    2: (3, 2),
    3: (4, 2),
    4: (4, 2),
    5: (5, 2),
    6: (5, 2),
}

PET_COST = 3
REROLL_COST = 1
STARTING_GOLD_AMOUNT = 10

class Shop:
    """Represents a shop that appears in a turn of super auto pets and lasts for a turn."""

    def __init__(self, pet_types: dict[str, PetType], food_types: dict[str, FoodType], turn: int, pack, buffs: list[tuple] = []):
        """Initializes the shop.

        Args:
            pet_types (dict): The dictionary of pet types in the game.
            food_types (dict): The dictionary of food types in the game.
            turn_number (int): The turn number of the shop.
            buffs (list): The list of buffs to apply to the shop.
        """
        self.pet_types = pet_types
        self.food_types = food_types
        self.turn = min(turn, 11)
        self.tier = TURNS_TO_TIERS.get(turn, 6)
        size = TIERS_TO_SIZE[self.tier]
        self.pet_max_count = size[0]
        self.food_max_count = size[1]
        self.pack = pack
        self.buffs = buffs
        self.gold = STARTING_GOLD_AMOUNT
        self._roll()

    def add_gold(self, amount):
        """Adds gold to the shop.

        Args:
            amount (int): The amount of gold to add.
        """
        self.gold += amount
            

    def _roll(self):
        """Rolls the shop."""

        pet_possibilities = []
        pet_weights = []
        for pet_type in self.pet_types.values():
            if hasattr(pet_type, 'probabilities') and self.turn in pet_type.probabilities:
                    pet_possibilities.append(pet_type)
                    pet_weights.append(pet_type.probabilities[self.turn][self.pack])

        rolled_pet_types = random.choices(
            population=pet_possibilities,
            weights=pet_weights,
            k=self.pet_max_count
        )
        self.pets = []
        for pet_type in rolled_pet_types: 
            self.pets.append(Pet(pet_type))

        for buff in self.buffs:
            self.buff_shop(buff["health"], buff["attack"])

        food_possibilites = []
        food_weights = []
        for food_type in self.food_types.values():
            if hasattr(food_type, 'probabilities') and self.turn in food_type.probabilities:
                    food_possibilites.append(food_type)
                    food_weights.append(food_type.probabilities[self.turn][self.pack])
                
        self.foods = random.choices(
            population=food_possibilites,
            weights=food_weights,
            k=self.food_max_count
        )

        

        

    def can_reroll(self):
        """Returns whether the shop can reroll."""
        return self.gold >= REROLL_COST

    def reroll(self):
        """Rerolls the shop."""

        if self.can_reroll():
            self.gold -= REROLL_COST
            self._roll()
            # logging.debug(f"Rerolled shop.")
            return True
        else:
            return False

    def buff_shop(self, health_amount: int, attack_amount: int):
        """Buffs the shop (until the next roll).

        Args:
            health_amount (int): The amount to add to the health of the pets.
            attack_amount (int): The amount to add to the attack of the pets.
        """
        for pet in self.pets:
            pet.buff(health_amount, attack_amount)

    def can_buy_food(self, food: FoodType | int):
        """Returns whether the shop can buy a food."""
        if isinstance(food, int):
            food = self.foods[food]
        return self.gold >= food.cost

    def can_buy_pet(self):
        """Returns whether the shop can buy a pet."""
        return self.gold >= PET_COST

    def buy_pet(self, pet: Pet | int):
        """Buys a pet from the shop."""
        if self.can_buy_pet():
            if isinstance(pet, int):
                pet = self.pets[pet]
            self.pets.remove(pet)
            self.gold -= PET_COST
            return pet
        else:
            return None

    def get_pets(self):
        """Returns the pets in the shop."""
        return self.pets

    def get_pet_count(self):
        """Returns the amount of pets in the shop."""
        return len(self.pets)

    def buy_food(self, food: FoodType | int):
        """Buys a food from the shop."""
        if isinstance(food, int):
            food = self.foods[food]
        if self.can_buy_food(food):
            self.foods.remove(food)
            self.gold -= food.cost
            return food
        return None

    def get_foods(self):
        """Returns the foods in the shop."""
        return self.foods

    def get_food_count(self):
        """Returns the amount of foods in the shop."""
        return len(self.foods)

    def add_pet_by_tier(self, tier):
        """Adds a pet to the shop."""
        if len(self.pets) < self.pet_size:
            pet_types_in_tier = PetType.by_tier(self.pet_types, tier)
            pet_type = random.choice(pet_types_in_tier)
            self.pets.append(Pet(pet_type))

    def clone(self):
        new_shop = Shop(self.pet_types, self.food_types, self.turn, self.pack, self.buffs)
        new_shop.gold = self.gold
        new_shop.pets = []
        for pet in self.pets:
            pet_clone = pet.clone()
            new_shop.pets.append(pet_clone)
        new_shop.foods = self.foods[:]
        return new_shop