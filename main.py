import json
from pickle import TRUE
import requests
import logging
from battler.battle_turn import BattleTurn
from mcts import mcts

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    # filename="sap_logs.log",
                    # filemode='w',
                    # encoding='utf-8'
                )


from pet_type import PetType
from food_type import FoodType
from status_type import StatusType
from battler.player import Player

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

def parse_food_types(source: dict | str):
    food_types = {}
    if isinstance(source, str):
        source = json.loads(source)
    food_types_json = source['foods']
    for food_id, food_type_json in food_types_json.items():
        food_types[food_id] = FoodType(food_type_json)

    return food_types

def parse_status_types(source: dict | str):
    status_types = {}
    if isinstance(source, str):
        source = json.loads(source)
    status_types_json = source['statuses']
    for status_id, status_type_json in status_types_json.items():
        status_types[status_id] = StatusType(status_type_json)
    return status_types


def fix_superauto_dot_pet_source(source: dict | str):
    """Some fixes for the specific source used, which has a few errors/incosistencies."""
    if isinstance(source, str):
        source = json.loads(source)
    pet_types_json = source['pets']
    for pet_id, pet_type_json in pet_types_json.items():
        if pet_id == 'pet-cow':
            for key, value in pet_type_json.items():
                if 'ability' in key:
                    ability_json = pet_type_json[key]
                    ability_json['effect']['food'] == 'food-milk'
                

    food_types_json = source['foods']
    for food_id, food_type_json in food_types_json.items():
        if food_type_json['ability']['trigger'] == "Buy":
            food_type_json['ability']['trigger'] = "BuyFood"
        if food_id == "food-milk":
            food_type_json['cost'] = 0
        if food_id == "food-sleeping-pill":
            food_type_json['cost'] = 1

    status_types_json = source['statuses']
    for status_id, status_type_json in status_types_json.items():
        if status_id == "status-splash-attack":
            status_type_json['ability']['trigger'] = "AfterAttack"
    return source
        
def pickle_best_teams(team_count=750):
    from battler.shop_turn import ShopTurn
    from battler.battle_turn import BattleTurn
    from battler.battle_turn import BattleResult

    teams = []
    for i in range(team_count):
        player = Player("Me")

        game = Game(pet_types, food_types, status_types, [player], "StandardPack")
        ShopTurn(player, game).play()
        teams.append(player.team.clone())

    count = 0
    wins = {}
    for i in range(len(teams)):
        team_1 = teams[i]
        for team_2 in teams[i+1:]:
            if team_1 != team_2:
                game = Game(pet_types, food_types, status_types, [player], "StandardPack")
                count += 1
                result = BattleTurn(team_1, team_2, game).play()
                if result == BattleResult.TEAM_1_WIN:
                    wins[team_1] = wins.get(team_1, 0) + 1
                elif result == BattleResult.TEAM_2_WIN:
                    wins[team_2] = wins.get(team_2, 0) + 1
                elif result == BattleResult.DRAW:
                    wins[team_1] = wins.get(team_1, 0) + 1
                    wins[team_2] = wins.get(team_2, 0) + 1

        print(f"{i}")
    
    # Sort by wins
    wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
    winners = []
    for winner, wins in wins:
        winners.append(winner)
        print(f"{winner}: {wins}")

    print(count)
    # import pickle
    # TEAMS_TO_SAVE = 250
    # with open("teams.pickle", "wb") as f:
    #     pickle.dump(winners[:TEAMS_TO_SAVE], f)

def test_games(game_count=5000):
    winners = {"Me": 0, "You": 0}
    for i in range(game_count):
        pack = "StandardPack"
        if i > game_count/2:
            pack = "ExpansionPack1"
        game = Game(pet_types, food_types, status_types, [Player("Me"), Player("You")], pack)


        winner = game.play()
        winners[winner] += 1
        print(i)
    print(winners)
    print(time.perf_counter() - t)

if __name__ == '__main__':
    source = requests.get(SOURCE_URL).json()
    source = fix_superauto_dot_pet_source(source)
    pet_types = parse_pet_types(source)
    status_types = parse_status_types(source)
    food_types = parse_food_types(source)
    import time 
    t = time.perf_counter()


    #mcts.simulate(pet_types, food_types, status_types, iterations=50)
    pickle_best_teams(team_count=750)

    # from game_integration.read_battle import read_battle
    # battle_json = json.load(open("battle.json"))
    # team, enemy_team = read_battle(pet_types, status_types, battle_json)
    # print(BattleTurn(team, enemy_team, Game(pet_types, food_types, status_types, [Player("Me"), Player("You")], "StandardPack")).play())



    print(f"Time: {time.perf_counter() - t}")
