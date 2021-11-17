import json


class PetType:
    """ Represents an pet type from Super Auto Pets. """

    def __init__(self, pet_json: dict | str):
        """Initializes a pet type from a JSON dictionary (or string) representing it."""
        if isinstance(pet_json, str):
            pet_json = json.loads(pet_json)
        self.name = pet_json['name']
        self.id = pet_json['id']
        self.tier = pet_json['tier']
        self.image_data = pet_json['image']
        self.health = pet_json['baseHealth']
        self.attack = pet_json['baseAttack']
        self.packs = pet_json['packs']
        self._init_abilities(pet_json)
        if "probabilities" in pet_json:
            self._init_probabilities(pet_json)

    def _init_abilities(self, pet_json):
        """Initializes the abilities of the pet type."""
        self.abilities = {}
        for level in range(1, 4):
            ability = pet_json.get(f"level{level}Ability")
            if ability:
                self.abilities[level] = ability

    def _init_probabilities(self, pet_json):
        """Initializes the probabilities of the pet type."""
        self.probabilities = {}
        for probability_json in pet_json["probabilities"]:
            if probability_json["kind"] == "shop":
                turn = int(probability_json["turn"].split("-")[1])
                self.probabilities[turn] = probability_json["perSlot"]
    
    def __str__(self):
        """Returns a string representation of the pet type."""
        return self.name

    @staticmethod
    def by_tier(pet_types, tier):
        pet_types_in_tier = []
        for pet_type in pet_types.values():
            if pet_type.tier == tier:
                pet_types_in_tier.append(pet_type)
        return pet_types_in_tier