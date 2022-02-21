from pet import Pet


class Team:
    """Represents a team of pets in super auto pets."""
    TEAM_SIZE = 5

    def __init__(self, pets=None, buffs=None):
        self.pets = pets
        if pets is None:
            self.pets = []
        self.buffs = buffs
        if buffs is None:
            self.buffs = []

    def can_add_pet(self):
        """Returns True if the team has room for another pet."""
        # Get amount of pets alive, because dead ones will be removed from the team so they don't count.
        pets_alive = 0
        for pet in self.pets:
            if pet.health > 0:
                pets_alive += 1
        return pets_alive < self.TEAM_SIZE

    def add_pet(self, pet, index=-1):
        """Add a pet to the team."""
        if self.can_add_pet():
            if index == -1:
                self.pets.append(pet)
            else:
                self.pets.insert(index, pet)
            return True
        else:
            return False


    def remove_pet(self, pet: Pet | int):
        """Remove a pet from the team."""
        if isinstance(pet, int):
            pet = self.pets[pet]
        if pet in self.pets:
            self.pets.remove(pet)
            return True
        else:
            return False

    def add_buff(self, health_amount, attack_amount):
        """Add a buff to the team."""
        self.buffs.append({"health": health_amount, "attack": attack_amount})

    def __str__(self) -> str:
        """Returns a string representation of the team."""
        return f"Team: {list(map(str, self.pets))}"

    def clone(self):
        """Returns a copy of the team."""
        new_team = Team(buffs=self.buffs[:])
        for pet in self.pets:
            pet_clone = pet.clone()
            pet_clone.team = new_team
            new_team.add_pet(pet_clone)
        return new_team


