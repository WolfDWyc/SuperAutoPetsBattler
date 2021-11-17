import json
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

from pet_type import PetType
from pet import Pet
from battler.game import Game

SOURCE_URL = "https://superauto.pet/api.json"

def parse_pet_types(source: dict | str):
    pet_types = {}
    if isinstance(source, str):
        source = json.loads(source)
    pet_types_json = source['pets']
    for pet_id, pet_type_json in pet_types_json.items():
        pet_types[pet_id]= PetType(pet_type_json)
    return pet_types

def fix_superauto_dot_pet_source(source: dict | str):
    """Some fixes for the specific source used, which has a few errors/incosistencies."""
    pass # Currently no bugs.
        
if __name__ == '__main__':
    source = requests.get(SOURCE_URL).json()
    pet_types = parse_pet_types(source)

    winners = {"Me": 0, "You": 0}
    for i in range(10):
        game = Game(pet_types, ["Me", "You"])
        winner = game.play()
        winners[winner] += 1
    print(winners)
