from pet_type import PetType
from food_type import FoodType
from status_type import StatusType
from pet import Pet
from team import Team


import json
with open('game_integration/game_pet_types.json') as f:
    game_pet_types = json.load(f)

with open('game_integration/game_status_types.json') as f:
    game_status_types = json.load(f)

def read_battle(pet_types, status_types, battle):


    team = Team()
    for item in battle["UserBoard"]["Minions"]["Items"]:
        if item:
            pet_type = pet_types[game_pet_types[str(item["Enum"])]]
            level = item["Level"]
            health = item["Health"]["Permanent"] + item["Health"]["Temporary"]
            attack = item["Attack"]["Permanent"] + item["Attack"]["Temporary"]
            status = None
            if item["Perk"]:
                status = status_types[game_status_types[str(item["Perk"])]]
            pet = Pet(pet_type, team, health, attack, level, -1, status)
            team.add_pet(pet)

    enemy_team = Team()
    for item in battle["OpponentBoard"]["Minions"]["Items"]:
        if item:
            pet_type = pet_types[game_pet_types[str(item["Enum"])]]
            level = item["Level"]
            health = item["Health"]["Permanent"] + item["Health"]["Temporary"]
            attack = item["Attack"]["Permanent"] + item["Attack"]["Temporary"]
            status = None
            if item["Perk"]:
                status = status_types[game_status_types[str(item["Perk"])]]
            pet = Pet(pet_type, team, health, attack, level, -1, status)
            enemy_team.add_pet(pet)

    return team, enemy_team


