from game.Table import Table
from queue import Queue
from dqn import simple_dqn

table = Table()
players = []

#state enconding: (5000 is the base amount of money for each player)
# player position: (player index / num players)
# player money: (current_money/ 5000)
# call amount (pot - [sum(every other players bet) or blind amount]
# cards in hand (2)
# community cards (5)
# whether or not each other player has raised this round (8)
# number of active players(numActive/totalPlayers) (8)
# betting round

raise_sizes = [0.01, 0.05, 0.2, 0.4, 0.5, 0.75, 1.0]

def action(player, action:int):
    #action = some int between 0 and 9

    raise_amounts = [raise_size * player.total_money for raise_size in raise_sizes]

    match action:
        case 9:
            player.fold()
        case 8:
            player.check()
        case 7: 
            player.call(table.current_raise)
            table.update_pot()
        case _:
            player.raise_(raise_amounts[action] + table.current_raise)
            table.update_pot()

def buildTable(numPlayers:int):
    global table
    global players
    for i in range(numPlayers):
        players.append(table.add_player())

def print_comm_cards():
    cards = table.game.community_cards
    for card in cards:
        if card == None:
            print("None", end = " ")
        else:
            print(card.get_true_name(), end = " ")
    print()
def is_legal_action(action_index, player_key):
    player = table.players[player_key]
    match action_index:
        case 9:
            if player.folded:
                return False # cant fold if the player has already folded
        case 8:
            if player.folded:
                return False # cant check if the player has folded
            if table.current_raise != player.raise_amount and player.total_money != 0:
                return False # if a player hasn't gone all in and they haven't matched the raise
            
        case 7:
            if table.current_raise == 0 or player.folded or player.total_bet == table.current_raise:
                return False # cant call if the player has folded or there is no raise
        case _:
            raise_amount = table.current_raise + table.get_blind(player_key)
            raise_amount += raise_sizes[action_index] * player.total_money # gets the raise amount
            if raise_amount > player.total_money: # cant raise more than the player has
                return False
    return True

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

def hand_loop():
    num_players = 4
    buildTable(num_players)

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
        print(table.current_stage)


if __name__ == "__main__":
    num_players = 8
    num_state_variables = 20
    num_outputs = 10

    player_networks = []
    #hand_loop()
    for _ in range(num_players):
        network = simple_dqn(num_state_variables, num_outputs)
        player_networks.append(network)
    
    """
    player_networks = []
    for _ in range(num_players):
        #generates a network for each "player"
        network = simple_dqn(num_state_variables, num_outputs)
        player_networks.append(network)

    buildTable(num_players) # builds table

    first_action = True 
    memory_buffers = [ReplayBuffer(5000) for _ in range(num_players)] # creates memory buffers for each player
    while table.has_a_player_raised() or first_action: #while a player has raised 
        
        first_action = False
        for player_ind in range(len(player_networks)): #each player does an action
            player_network = player_networks[player_ind]
            player = players[player_ind]

            state = table.get_state()

            q_values = player_network.get_model_output(state)
            current_max = q_values[0]

            max_index = 0 # argmax 
            for val_index in range(len(q_values)):
                new_max = max(current_max, q_values[val_index])
                if new_max != current_max:
                    max_index = val_index
                    current_max = new_max
            
            
            action(player, max_index) # do action

            next_state = table.get_state() # get the next state

            memory = Memory(state, max_index, 0, next_state, table.hand_done)#generate a memory
            memory_buffers[player_ind].store_memory(memory) # stores memory

        for memory_buffer in memory_buffers: # last memory is the memory that is the end of the table
            memory_buffer.buffer[-1].is_done = True          
            # assign rewards
    #on completion, apply a retroactive reward modifier if the player won money
    #if the player lost money apply a negative reward modifier
    #if the player didn't lose or win anything apply a small negative modifier

    for player in players:
        player.raise_(raise_amount)
        raise_amount += 1
    for i in range(2):
        table.game.deal_hands()
        table.advance_stage()
        table.game.get_community_cards()

        print_comm_cards()
        table.advance_stage()
        table.game.get_community_cards()
        table.advance_stage()

        table.game.print_hands()


        table.advance_stage()

                
        for player in players:
            print(player.total_money)
    
    
    #table.game.rank_hands()
    """