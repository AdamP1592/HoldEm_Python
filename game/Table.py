import random
from game.HoldEm import HoldEm
from game.Player import Player

class Table:
    
    def __init__(self):
        self.game = HoldEm(1)
        self.stages = {"pre-flop":self.game.flop, "flop": self.game.turn, "turn": self.game.river, "river": self.game.reset }
        self.current_stage = "pre-flop"

        self.players = {}
        self.game.players = self.players # shared instance
        self.community_cards = self.game.community_cards #shared instance
        self.pot = self.game.pot # shared instance

        self.current_raise = 0

    def add_player(self):
        player_id = str(random.getrandbits(128))
        p = Player()
        self.players[player_id] = p
        return p
    
    def remove_player(self, player_key):
        self.players.pop(player_key)

    def advance_stage(self):
        self.stages[self.current_stage]()

        stageKeys = list(self.stages.keys())
        ind = stageKeys.index(self.current_stage)


        self.current_stage = stageKeys[(ind + 1) % len(stageKeys)]

        

        
