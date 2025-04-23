import random
from game.HoldEm import HoldEm
from game.Player import Player

class Table:
    
    def __init__(self):
        self.game = HoldEm(1)
        self.stages = {"pre-flop":self.game.flop, "flop": self.game.turn, "turn": self.game.river, "river": self.reset_hand }

        self.hand_done = False
        self.current_stage = "pre-flop"

        self.players = {}

        self.total_raises = {}
        self.game.players = self.players # shared instance
        self.community_cards = self.game.community_cards #shared instance
        self.pot = self.game.pot # shared instance

        self.big_blind_key = None
        self.small_blind_key = None

        self.big_blind = 50
        self.small_blind = 25

        self.current_raise = 50
        self.blind_applied = False

    def get_prev_winner(self):
        return self.game.prev_winners
    
    def get_state(self, player_key):

        base_money = 5000
        num_players = len(self.players)

        player_keys = list(self.players.keys())

        player_index = player_keys.index(player_key)
        starting_player_key = self.get_starting_player()
        starting_player_ind = player_keys.index(starting_player_key)

        state = [       
                 starting_player_ind / num_players,
                 player_index / num_players,
                 self.players[player_key].total_money / base_money,
                 self.pot / base_money,
                 self.current_raise / base_money
                ]
        

        #encodes stage
        stage_names = list(self.stages.keys())
        current_stage_ind = stage_names.index(self.current_stage)
        for stage in self.stages.keys():
            if stage == current_stage_ind:
                state.append(1.0)
            else:
                state.append(0)

        #grabs whether or not each player has folded, their total bet, and their current raise
        for key in self.players:
            player = self.players[key]
            if player.folded:
                state.append(0)
            else:
                state.append(1)

            state.append(player.total_bet/base_money)
            state.append(player.raise_amount/base_money)
            state.append(self.total_raises[key])
        
        #encodes player cards in one-hot style encoding
        hole_map = [0] * 52
        cards_in_hand = self.players[player_key].get_hand().get_cards()
        for card in cards_in_hand:
            idx = card.get_encoded_value()
            hole_map[idx] = 1

        state.extend(hole_map)

        #encodes community cards in one‑hot 
        board_map = [0] * 52
        for card in self.community_cards:
            if card != None:
                idx = card.get_encoded_value()
                board_map[idx] = 1

        state.extend(board_map)

        return state

    def update_pot(self):
        self.pot = 0
        for player_key in self.players:

            self.total_raises[player_key] += 1
            player = self.players[player_key]
            self.pot += player.total_bet
            self.current_raise = max(self.current_raise, player.raise_amount)

    def get_starting_player(self) -> int:
        player_keys = list(self.players.keys())
        for key_ind in range(len(player_keys)):
            if player_keys[key_ind] == self.big_blind_key:
                return player_keys[(key_ind + 1) % len(player_keys)]
        
    def apply_blind(self):
        if not self.blind_applied:
            big_blind_player = self.players[self.big_blind_key]
            big_blind_player.raise_(self.big_blind)

            small_blind_player = self.players[self.small_blind_key]
            small_blind_player.raise_(self.small_blind)

            self.blind_applied = True

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
        self.rotate_blinds()
        self.blind_applied = False
        self.game.reset()
        for player_key in self.total_raises:
            self.total_raises[player_key] = 0
    
    def get_winners(self):
        return self.game.last_winners

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

    def deal(self):
        self.game.deal_hands()

    def add_player(self):
        player_id = str(random.getrandbits(128))

        if self.small_blind_key == None:
            self.small_blind_key = player_id
        elif self.big_blind_key == None:
            self.big_blind_key = player_id

        p = Player()
        self.players[player_id] = p
        self.total_raises[player_id] = 0
        return p
    
    def remove_player(self, player_key):
        self.players.pop(player_key)

    def advance_stage(self):
        
        if self.has_a_player_raised():
            return
        
        for player_key in self.players:
            self.players[player_key].next_turn()
            
        self.stages[self.current_stage]()

        self.current_raise = 0
        stageKeys = list(self.stages.keys())
        ind = stageKeys.index(self.current_stage)

        self.current_stage = stageKeys[(ind + 1) % len(stageKeys)]
    
    def print_comm_cards(self):
        for card in self.community_cards:
            if card != None:
                print(card.get_true_name(), end = " ")
        print()