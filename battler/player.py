from team import Team
STARTING_HEALTH = 10

class Player:

    def __init__(self, name: str):
        self.name = name
        self.health = STARTING_HEALTH
        self.team = Team()

    def __str__(self) -> str:
        """Returns a string representation of the player."""
        player_string = ""
        player__info_string = f"-------------- {self.name} ------- HP: {self.health} -------\n"
        player_string += player__info_string
        player_string += f"{self.team}\n"
        player_string += "-" * len(player__info_string)
        return player_string
