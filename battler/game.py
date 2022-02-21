from battler.player import Player
from battler.battle_turn import BattleTurn, BattleResult
from battler.shop_turn import ShopTurn
import logging
from utils.concat import concat_strings_horizontally

TURNS_TO_LIVES = {
    1: 1,
    2: 1,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
}

class Game:
    def __init__(self, pet_types, food_types, status_types, players=[], pack="StandardPack"):
        self.pack = pack
        self.triggers = {}
        for pet_id, pet_type in pet_types.items():
            for ability in pet_type.abilities.values():
                self.triggers[ability["trigger"]] = self.triggers.get(ability["trigger"], set()) | {pet_id}
        for food_id, food_type in food_types.items():
            ability = food_type.ability
            self.triggers[ability["trigger"]] = self.triggers.get(ability["trigger"], set()) | {food_id}
        for status_id, status_type in status_types.items():
            ability = status_type.ability
            self.triggers[ability["trigger"]] = self.triggers.get(ability["trigger"], set()) | {status_id}
        for pet_id, pet_type in pet_types.items():
            for ability in pet_type.abilities.values():
                if ability["effect"]["kind"] == "TransferAbility": # A transfered ability can become any type of ability
                    for trigger in self.triggers:
                        self.triggers[trigger] |= {pet_id}

        self.pet_types = {pet_id: pet_type for pet_id, pet_type in pet_types.items() if pack in pet_type.packs}
        self.food_types = {food_id: food_type for food_id, food_type in food_types.items() if pack in food_type.packs}
        self.status_types = status_types

        self.players = players
        self.battle_results = []
        self.turn = 1

    def play(self):
        logging.info(str(self))
        while all(player.health > 0 for player in self.players):
            for player in self.players:
                logging.info(f"Shop turn for player {player.name}:")
                ShopTurn(player, self).play()
            # TODO: Support more than 2 players
            battle_result = BattleTurn(self.players[0].team, self.players[1].team, self).play()
            if battle_result == BattleResult.TEAM_1_WIN:
                self.players[1].health -= TURNS_TO_LIVES.get(self.turn, 3)
                self.battle_results.append({"result": BattleResult.TEAM_1_WIN, "winner": self.players[0], "loser": self.players[1]})
            elif battle_result == BattleResult.TEAM_2_WIN:
                self.players[0].health -= TURNS_TO_LIVES.get(self.turn, 3)
                self.battle_results.append({"result": BattleResult.TEAM_2_WIN, "winner": self.players[1], "loser": self.players[0]})
            else:
                self.battle_results.append({"result": BattleResult.DRAW, "winner": None, "loser": None})


            self.turn += 1
            logging.info(str(self))

        if self.players[0].health > 0:
            logging.info(f"{self.players[0].name} wins!")
            return self.players[0].name
        else:
            logging.info(f"{self.players[1].name} wins!")
            return self.players[1].name



    def __str__(self) -> str:
        """Returns a string representation of the team."""
        game_string = "\n"
        game_string_info = f"--------------- {' vs '.join(map(lambda p: p.name, self.players))} -------- Turn: {self.turn} -------\n"
        game_string += game_string_info

        player_strings = [str(player) for player in self.players]
        # Merge player strings hortizontally 
        game_string += concat_strings_horizontally(player_strings, "|") + "\n"
        game_string += "-" * len(game_string_info) 

        return game_string