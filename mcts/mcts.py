import logging
from battler.game import Game
from battler.player import Player
from battler.shop_turn import ShopTurn
from team import Team
from battler.battle_turn import BattleTurn, BattleResult
from montecarlo.node import Node
from montecarlo.montecarlo import MonteCarlo


# Monte-Carlo Tree Search

import pickle
with open("teams.pickle", "rb") as f:
    teams: list[Team] = pickle.load(f)

class TurnState:
    def __init__(self, shop_turn):
        self.shop_turn = shop_turn
        self.score = None

    def clone(self):
        return TurnState(self.shop_turn.clone())


def simulate(pet_types, food_types, status_types, iterations=50):
    """
    Simulate the game for a given number of iterations.
    """
    game = Game(pet_types, food_types, status_types, players=[Player("Dummy")])

    def child_finder(node, self):
        # TODO: End turn events
        move_options = node.state.shop_turn.get_move_options()[0]
        if node.state.shop_turn.are_moves_left(move_options):
            for move in move_options:
                child = Node(node.state.clone())
                child.state.shop_turn.play_move(move)
                node.add_child(child)
        else:
            child = Node(node.state.clone())
            team = child.state.shop_turn.team
            score = 0
            for opponent in teams:
                result = BattleTurn(team, opponent, game).play() # Rework battle turn to not depend on game
                if result == BattleResult.TEAM_1_WIN:
                    score += 1
                elif result == BattleResult.TEAM_2_WIN:
                    score -= 1
                elif result == BattleResult.DRAW:
                    score += 0.5
            child.state.score = score
            node.add_child(child)


    def node_evaluator(node, self):
        return node.state.score

    root = Node(TurnState(ShopTurn(game.players[0], game))) # TODO: Rework shop turn to not depend on player and game
    mc = MonteCarlo(root)
    mc.child_finder = child_finder
    mc.node_evaluator = node_evaluator

    mc.simulate(890)
    for i in range(5):
        print(mc.root_node.state.shop_turn.get_move_options()[0])
        root_node = mc.make_choice()
        print(str(root_node.state.shop_turn.team))
        mc.root_node = root_node







