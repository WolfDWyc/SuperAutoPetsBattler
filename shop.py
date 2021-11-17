import random

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
    12: 6
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

    def __init__(self, pet_types: list[PetType], turn: int, pack, buffs: list[tuple] = []):
        """Initializes the shop.

        Args:
            pet_types (dict): The dictionary of pet types in the game.
            turn_number (int): The turn number of the shop.
            buffs (list): The list of buffs to apply to the shop.
        """
        self.pet_types = pet_types
        self.turn = turn
        self.tier = TURNS_TO_TIERS.get(turn, 6)
        size = TIERS_TO_SIZE[self.tier]
        self.pet_size = size[0]
        self.food_count = size[1]
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

        population = []
        weights = []
        for pet_type in self.pet_types.values():
            if hasattr(pet_type, 'probabilities'):

                if self.turn in pet_type.probabilities:
                    population.append(Pet(pet_type))
                    weights.append(pet_type.probabilities[self.turn][self.pack])

        self.pets = random.choices(
            population=population,
            weights=weights,
            k=self.pet_size
        )

        for buff in self.buffs:
            self.buff_shop(buff["health"], buff["attack"])

    def can_reroll(self):
        """Returns whether the shop can reroll."""
        return self.gold >= REROLL_COST

    def reroll(self):
        """Rerolls the shop."""
        if self.can_reroll():
            self.gold -= REROLL_COST
            self._roll()
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
            pet.add_health(health_amount)
            pet.add_attack(attack_amount)

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
        """Returns the size of the shop."""
        return len(self.pets)

    def add_pet_by_tier(self, tier):
        """Adds a pet to the shop."""
        if len(self.pets) < self.pet_size:
            pet_types_in_tier = PetType.by_tier(self.pet_types, tier)
            pet_type = random.choice(pet_types_in_tier)
            self.pets.append(Pet(pet_type))