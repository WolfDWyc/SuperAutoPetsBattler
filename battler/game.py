from battler.player import Player
from battler.battle_turn import BattleTurn, BattleResult
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
    def __init__(self, pet_types, player_names=[], pack="StandardPack"):
        self.pack = pack

        self.pet_types = {pet_id: pet_type for pet_id, pet_type in pet_types.items() if pack in pet_type.packs}
        self.players = []
        self.turn = 1
        for player_name in player_names:
            self.players.append(Player(self, player_name))

    def play(self):
        logging.info(str(self))
        while all(player.health > 0 for player in self.players):
            for player in self.players:
                logging.info(f"Shop turn for player {player.name}:")
                player.play_shop_turn()
            # TODO: Support more than 2 players
            battle_result = BattleTurn(self.players[0].team, self.players[1].team, self).play()
            if battle_result == BattleResult.TEAM_1_WIN:
                self.players[1].health -= TURNS_TO_LIVES.get(self.turn, 3)
            elif battle_result == BattleResult.TEAM_2_WIN:
                self.players[0].health -= TURNS_TO_LIVES.get(self.turn, 3)

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