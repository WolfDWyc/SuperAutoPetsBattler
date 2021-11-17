from battler.shop_turn import ShopTurn
from team import Team
STARTING_HEALTH = 10

class Player:

    def __init__(self, game, name: str):
        self.game = game
        self.name = name
        self.health = STARTING_HEALTH
        self.team = Team()

    def play_shop_turn(self):
       ShopTurn(self.team, self.game.pet_types, self.game.turn, self.game.pack).play()

    def __str__(self) -> str:
        """Returns a string representation of the player."""
        player_string = ""
        player__info_string = f"-------------- {self.name} ------- HP: {self.health} -------\n"
        player_string += player__info_string
        player_string += f"{self.team}\n"
        player_string += "-" * len(player__info_string)
        return player_string
