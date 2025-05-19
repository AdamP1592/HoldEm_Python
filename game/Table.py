import random
from collections import OrderedDict
from game.HoldEm import HoldEm
from game.Player import Player


class Table:
    
    def __init__(self):
        self.game = HoldEm(1)
        self.stages = {"pre-flop":self.game.flop, "flop": self.game.turn, "turn": self.game.river, "river": self.reset_hand }

        self.hand_done = False
        self.current_stage = "pre-flop"

        self.players = {}
        self.game.players = self.players # shared instance

        self.total_raises = {}
        self.community_cards = self.game.community_cards #shared instance
        self.pot = self.game.pot # shared instance

        self.big_blind_key = None
        self.small_blind_key = None

        self.big_blind = 250
        self.small_blind = 125

        self.current_raise = 250
        self.blind_applied = False

    def get_prev_winner(self):
        return self.game.last_winners
    
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
        hand = self.players[player_key].get_hand()
        cards_in_hand = []
        if hand:
            cards_in_hand = hand.get_cards()
        for card in cards_in_hand:
            idx = card.get_encoded_value() - 1 #converts value (1, 52) to index(0, 51)
            hole_map[idx] = 1

        state.extend(hole_map)

        #encodes community cards in one‑hot 
        board_map = [0] * 52
        for card in self.community_cards:
            if card != None:
                idx = card.get_encoded_value() - 1
                
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
        active_players = self.get_players_in_hand(self.big_blind_key)
        #1 to the right of the big blind
        return active_players[1][0]

    def apply_blind(self):


        if not self.blind_applied:
            big_blind_player = self.players[self.big_blind_key]
            big_blind_player.raise_(self.big_blind)

            small_blind_player = self.players[self.small_blind_key]
            small_blind_player.raise_(self.small_blind)

            self.blind_applied = True

        self.current_raise = self.big_blind
        self.update_pot()

    def rotate_blinds(self, debug = False):
        #gets active player queue, where the starting player is the current big blind
        active_player_keys = [player_key for player_key, _, _ in self.get_players_in_hand(self.big_blind_key)]
        
        if debug:
            print("All players: ", self.players.keys())
            print("Active Players:", active_player_keys)
            print("Old big blind: ", self.big_blind_key)
            print("Old small blind: ", self.small_blind_key)

        #shifts the blind over by 1
        num_active_players = len(active_player_keys)
        if num_active_players < 2:
            if debug:
                print(f"[rotate blinds]: only {num_active_players}")
            return False
        
        self.big_blind_key = active_player_keys[-1] # big blind is 1 to the left
        self.small_blind_key = active_player_keys[-2] # small blind is one to the left of the new big blind

        if debug:
            print("New Big Blind: ", self.big_blind_key)
            print("New Small Blind: ", self.small_blind_key)

        return True

    def reset_hand(self):
        self.current_stage = "pre-flop"
        self.game.community_cards_index = 0
        self.current_raise = 50

        self.rotate_blinds()
        self.blind_applied = False

        print("Resetting Hand")
        
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
        
        stage_keys = list(self.stages.keys())
        ind = stage_keys.index(self.current_stage)

        for player_key in self.players:
            self.players[player_key].next_turn()
            
        self.stages[self.current_stage]()

        self.current_raise = 0
        
        self.current_stage = stage_keys[(ind + 1) % len(stage_keys)]

    def get_players_in_hand(self, starting_player_key):
        unfolded_players = []
        player_keys = list(self.players.keys())

        starting_player_index = player_keys.index(starting_player_key)

        for player_index in range(len(self.players)):
            current_index = (starting_player_index + player_index) % (len(self.players))
            current_player_key = player_keys[current_index]
            player = self.players[current_player_key]

            #if the player has no money, but they have made a bet for this round,
            if not player.bust:
                #print(f"Seat:{current_index}, folded:{player.folded}, raise:{player.total_bet}, current_raise:{self.current_raise} {'in' if not player.folded else 'out'}")
                unfolded_players.append((current_player_key, player, current_index))

        return unfolded_players
    
    def any_player_all_in(self) -> bool:
        for player_key in self.players:
            if self.players[player_key].all_in == True:
                return True
        return False
    def get_active_players(self, starting_player_key):
        players_to_move = []
        player_keys = list(self.players.keys())

        starting_player_index = player_keys.index(starting_player_key)

        for offset in range(len(self.players)):
            current_index = (starting_player_index + offset) % (len(self.players))
            current_player_key = player_keys[current_index]
            player = self.players[current_player_key]

            #if the player has no money, but they have made a bet for this round,
            #add them to the queue
            player_busted = (player.total_money < 1 and player.total_bet < 1)
            player_all_in = (player.total_money == 0 and player.total_bet > 0)
            #print(f"Player: {current_player_key}, Folded: {player.folded}, Bust: {player_busted}, All in: {player_all_in}")
            # not (player_busted or player_all_in)
            print(f"Player: {current_index}, All In:{player.all_in}, Bust: {player.bust}, Fold: {player.folded} ")
            if not player.folded and not player.all_in and not player.bust:
                #print(f"Seat:{current_index}, folded:{player.folded}, raise:{player.total_bet}, current_raise:{self.current_raise} {'in' if not player.folded else 'out'}")
                players_to_move.append((current_player_key, player, current_index))

        return players_to_move
    def betting_round_complete(self):
        for player in self.players.values():
            # if player could make an action but hasn't, return false
            if not(player.folded or player.checked or player.raised or player.bust or player.all_in):
                return False
        return True
    def is_showdown(self) -> bool:
        #arbitrary starting point
        active_players = self.get_active_players(self.big_blind_key)
        players_still_in = self.get_players_in_hand(self.big_blind_key)
        
        # if there is only 1 player left then the player doesnt show hands
        if len(players_still_in) < 2:
            return False

        #if there is 1 or 0 players that havent: bust, gone all in, or folded
        if len(active_players) <= 1:
            return True
        #if its the end of the final round
        elif self.current_stage == "river" and self.betting_round_complete():
            return True


    def print_table_state(self, human_player_key, display_hands = False):
        display_cards = False
        if self.is_showdown() or display_hands == True:
            display_cards = True

        box_extension = ""

        header_top =    "+--------+-----------+----------+------------+"
        header_labels = "| Player |   Stack   |   Bet    |   Action   |"
        header_bottom = "+--------+-----------+----------+------------+"

        #reformats header if state demands cards need to be displayed
        if display_cards:
            box_extension += ("-" * 11) + "+" # Extension for border

            header_top += box_extension
            header_labels += "   Cards" + (" " * 3) + "|"
            header_bottom += box_extension

        print(header_top)
        print(header_labels)
        print(header_bottom)

        # Every time there is a " " * (number - len(value)) that's just padding the box with spaces.
        # Could just use .ljust() but the result is the same exact thing, but I learned about it
        # after doing this
        for index, key in enumerate(self.players):
            player = self.players[key]
            #rounds to the nearest whole number, converts to str
            player_money = str(int(player.total_money))
            player_bet = str(int(player.raise_amount))
            # Player col 
            row = f"| P{index}" + (" " * 5) 
            # Stack col
            row += f"| ${player_money}" + (" " * (9 - len(player_money)))
            # Bet col
            row += f"| ${player_bet}" + (" " * (8 - len(player_bet)))
            action = ""
            if player.folded:
                action = "Folded"
            elif player.called:
                action = "Called"
            elif player.checked:
                action = "Checked"
            elif player.raised:
                action = "Raised"

            row += f"| {action} " + (" " * (10 - len(action)))

            if display_cards:
                hand = str(player.get_hand())
                row += f"| {hand}" + (" " * (10 - len(hand)))
                row += ""
            row += "|"

            print(row)
        
        #dont need to rebuild the border edge, just use the existing top
        print(header_top)
 
    def print_comm_cards(self):
        for card in self.community_cards:
            if card != None:
                print(card.get_true_name(), end = " ")
        print()