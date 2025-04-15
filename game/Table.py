import random
from game.HoldEm import HoldEm
from game.Player import Player

class Table:
    
    def __init__(self):
        self.game = HoldEm(1)
        self.stages = {"pre-flop":self.game.flop, "flop": self.game.turn, "turn": self.game.river, "river": self.game.reset }

        self.hand_done = False
        self.current_stage = "pre-flop"

        self.players = {}
        self.game.players = self.players # shared instance
        self.community_cards = self.game.community_cards #shared instance
        self.pot = self.game.pot # shared instance

        self.big_blind_key = None
        self.small_blind_key = None

        self.big_blind = 50
        self.small_blind = 25

        self.current_raise = 50

    def get_starting_player(self):
        player_keys = list(self.players.keys())
        for key_ind in range(len(player_keys)):
            if player_keys[key_ind] == self.big_blind_key:
                return player_keys[(key_ind + 1) % len(player_keys)]
        
    def apply_blind(self):
        big_blind_player = self.players[self.big_blind_key]
        big_blind_player.raise_(self.big_blind)

        small_blind_player = self.players[self.small_blind_key]
        small_blind_player.raise_(self.small_blind)


    def rotate_blinds(self):
        player_keys = list(self.players.keys())
        for key_ind in range(len(player_keys)):
            if player_keys[key_ind] == self.big_blind_key:
                #small blind starts at player_index 1
                #big blind starts at player_index 0
                #so shift big blind to the small blind and then shift the small blind to 2 indexes over
                self.big_blind_key = player_keys[(key_ind + 1) % len(player_keys)]#shifts the big blind over 1
                self.small_blind_key = player_keys[key_ind]
                return
                
    def reset_hand(self):
        self.game.reset()

    def get_blind(self, player_key):
        if player_key == self.big_blind_key:
            return self.big_blind
        elif player_key == self.small_blind_key:
            return self.small_blind
        return 0

    def has_a_player_raised(self):
        for player_key in self.players:
            if self.players[player_key].raised:
                return True
        return False

    def add_player(self):
        player_id = str(random.getrandbits(128))

        if self.small_blind_key == None:
            self.small_blind_key = player_id
        elif self.big_blind_key == None:
            self.big_blind_key = player_id

        p = Player()
        self.players[player_id] = p
        return p
    
    def remove_player(self, player_key):
        self.players.pop(player_key)

    def advance_stage(self):
        if self.has_a_player_raised():
            return
        self.stages[self.current_stage]()

        stageKeys = list(self.stages.keys())
        ind = stageKeys.index(self.current_stage)

        self.current_stage = stageKeys[(ind + 1) % len(stageKeys)]
    
    def print_comm_cards(self):
        for card in self.community_cards:
            if card != None:
                print(card.get_true_name(), end = " ")
        print()