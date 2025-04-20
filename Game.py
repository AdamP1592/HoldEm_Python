from game.Table import Table
from queue import Queue
#from dqn import simple_dqn

from GameTests import *

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

def build_table(numPlayers:int):
    global table
    global players
    for i in range(numPlayers):
        players.append(table.add_player())

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


if __name__ == "__main__":
    num_players = 8
    num_state_variables = 20

    num_outputs = 112 + (num_players * 3)

    #test_hand()

    player_networks = []

    print(num_outputs)
    test_state()
    
    table.reset_hand()
    """
    for _ in range(num_players):
        network = simple_dqn(num_state_variables, num_outputs)
        player_networks.append(network)
    
    
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