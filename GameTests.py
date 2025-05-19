from Game import *
from dqn.ReplayBuffer import ReplayBuffer
from dqn.Memory import Memory
def test_hand():
    num_players = 4
    build_table(num_players)

    table.apply_blind()
    table.update_pot()
    table.deal()

    player_key_list = list(table.players.keys())
    starting_player_key = table.get_starting_player()

    round_end_ind = player_key_list.index(starting_player_key)

    pre_flop = True # to ensure the current hand is the inital pre-flop
    while table.current_stage != "pre-flop" or pre_flop:
        pre_flop = False
        
        i = 0
        #iterate over the length of the players.
        #if a player raises, shift round_end_ind to the current index and then
        #reset i to 0
        while i < num_players:
            current_player_index = (round_end_ind + i) % num_players
            current_player_key = player_key_list[current_player_index]
            current_player = table.players[current_player_key]
            #skip player if he has folded
            if current_player.folded:
                i+=1
                continue

            #check if there is only one active player they win
            active_players = [p_key for p_key, p in table.players.items() if not p.folded]
            if len(active_players) == 1:
                table.player_won(active_players[0])
                table.reset_hand()
                return  # or return, if in function
            
            print("Current Pot: ", table.pot)
            print("Current Raise Amount", table.current_raise)
            print("Player: ", current_player_index)

            table.print_comm_cards()

            for player_key in player_key_list:
                current_player_bet = table.players[player_key].total_bet
                if table.players[player_key].folded:
                    print("Folded", end = " ")
                    continue
                elif player_key == current_player_key:
                    print("*", end="")
                print(current_player_bet, end=" ")
                
            print()
            current_player.print_hand()

            print("Actions:\n\t0-6 raise\n\t7:Call\n\t8:check\n\t9:fold")
            player_action = int(input("Enter action "))
            while True:
                if is_legal_action(player_action, current_player_key):
                    print(table.players[current_player_key])
                    action(table.players[current_player_key], player_action)
                    if player_action < 7 and player_action >= 0:
                        i = 0
                        round_end_ind = current_player_index + 1
                    else:
                        i+=1
                    break
                else:
                    debug_valid_action_info(current_player_key, player_action)
                player_action = int(input("Enter action "))

            
        table.advance_stage()
        table.rotate_blinds()
        print(table.current_stage)

def debug_valid_action_info(player_key, action_index):
    player = table.players[player_key]
    print("=== ILLEGAL ACTION DEBUG ===")
    print(f"Player Key:        {player_key}")
    print(f"Action Index:      {action_index}")
    print(f"Folded?            {player.folded}")
    print(f"Checked?           {player.checked}")
    print(f"Raised?            {player.raised}")
    print(f"Player.raise_amount: {player.raise_amount}")
    print(f"Player.total_bet:    {player.total_bet}")
    print(f"Player.total_money:  {player.total_money}")
    print(f"Table.current_raise: {table.current_raise}")
    blind_amt = table.get_blind(player_key)
    print(f"Blind amount:        {blind_amt}")
    if action_index == 7:
        # call case
        owed = table.current_raise - player.total_bet
        print(f"Amount needed to call: {owed}")
    elif action_index in range(0, 7):
        # raise case
        rs = raise_sizes[action_index]
        computed = table.current_raise + blind_amt + rs * player.total_money
        print(f"Raise size frac:      {rs}")
        print(f"Computed raise_amt:   {computed}")
    print("============================")


def print_comm_cards():
    cards = table.game.community_cards
    for card in cards:
        if card == None:
            print("None", end = " ")
        else:
            print(card.get_true_name(), end = " ")
    print()



def test_state():
    build_table(3)
    table.apply_blind()
    table.update_pot()
    table.deal()
    
    for player_key in table.players:
        state = table.get_state(player_key)

        print(state)
        print(len(state))

    table.advance_stage()

    for player_key in table.players:
        state = table.get_state(player_key)

        print(state)
        print(len(state))

def test_memory_buffer():
    buff1 = ReplayBuffer(100)
    buff2 = ReplayBuffer(10)
    for i in range(50):
        pass

def test_rotating_blind_with_bust():
    build_table(3)
    keys = list(table.players.keys())
    table.apply_blind()
    table.deal()

    #continuously advance stages until the hand is reset
    table.advance_stage()
    while table.current_stage != "pre-flop":
        table.advance_stage()

    #sets the middle player money to nothing
    table.players[keys[1]].total_money = 0
    table.rotate_blinds(debug = True)

def test_display():
    build_table(3)
    table.apply_blind()
    table.deal()
    first_key = list(table.players.keys())[0]
    table.print_table_state(first_key, True)

    table.players[first_key].total_money += 10000.05
    table.print_table_state(first_key, True)

    table.players[first_key].total_money += 100000.05
    table.print_table_state(first_key, True)

    table.players[first_key].raise_(50000)
    table.print_table_state(first_key, True)

    