import logging
import random




def get_targets(ability_effect, event_data=None, pet=None, team_pets=None, enemy_pets=None, team_pets_snapshot=None):
    ability_target = ability_effect.get("target")
    if not ability_target:
        ability_target = ability_effect.get("to")
    
    affected_pets = []
    match ability_target["kind"]:
        case "Self":
            affected_pets.append(pet)
        case "TriggeringEntity":
            affected_pets.append(event_data["pet"])
        case "PurchaseTarget":
            affected_pets.append(event_data["purchase_target"])
        case "RandomFriend":
            pets = team_pets[:]
            if pet and pet in pets:
                pets.remove(pet)
            affected_pets += random.sample(pets, min(ability_target["n"], len(pets)))
        case "EachFriend":
            pets = team_pets[:]
            if pet and pet in pets:
                pets.remove(pet)
            affected_pets += pets
        case "Level2And3Friends":
            pets = team_pets[:]
            if pet and pet in pets:
                pets.remove(pet)
            affected_pets += [pet for pet in pets if pet.level in [2, 3]]
        case "DifferentTierAnimals":
            tiers = set()
            for pet in team_pets:
                if pet.pet_type.tier not in tiers:
                    tiers.add(pet.pet_type.tier)
                    affected_pets.append(pet)
        case "AdjacentFriends":
            pets = team_pets
            index = pets.index(pet)
            for pet_index in [index - 1, index + 1]:
                if 0 <= pet_index < len(pets):
                    pet = pets[pet_index]
                    affected_pets.append(pet)
        case "LeftMostFriend":
            pets = team_pets
            if len(pets) > 0:
                affected_pets.append(pets[0])
        case "RightMostFriend":
            pets = team_pets
            if len(pets) > 0:
                affected_pets.append(pets[-1])
        case "FriendBehind":
            affected_pets = []
            pets = team_pets
            pet_amount = ability_target["n"]
            index = pets.index(pet) - 1
            for pet_index in range(index, index - pet_amount, -1):
                if 0 <= pet_index < len(pets):
                    affected_pets.append(pets[pet_index])
        case "FriendAhead":
            pets = team_pets
            pet_amount = ability_target["n"]
            index = pets.index(pet) + 1
            for pet_index in range(index, index + pet_amount):
                if 0 <= pet_index < len(pets):
                    affected_pets.append(pets[pet_index])
        case "All":
            affected_pets += team_pets + enemy_pets
        case "EachEnemy":
            affected_pets += enemy_pets
        case "RandomEnemy":
            affected_pets += random.sample(enemy_pets, min(ability_target["n"], len(enemy_pets)))
        case "FirstEnemy":
            if len(enemy_pets) > 0:
                affected_pets.append(enemy_pets[-1])
        case "LastEnemy":
            if len(enemy_pets) > 0:
                affected_pets.append(enemy_pets[0])
        case "LowestHealthEnemy":
            if len(enemy_pets) > 0:
                lowest_health_pet = min(enemy_pets, key=lambda pet: pet.health)
                affected_pets.append(lowest_health_pet)
        case "AdjacentAnimals":
            if len(enemy_pets) > 0:
                affected_pets.append(enemy_pets[-1])
            index = team_pets.index(event_data["pet"])
            if index != 0:
                affected_pets.append(team_pets[index - 1])
        case "HighestHealthEnemy":
            if enemy_pets:
                affected_pets.append(max(enemy_pets, key=lambda pet: pet.health))
    
    return affected_pets



    