from game.Table import Table
from dqn import *

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

def action(player, action:int):
    #action = some int between 0 and 9

    raise_sizes = [0.05, 0.1, 0.2, 0.4, 0.5, 0.75, 1.0]
    raise_amounts = [raise_size * player.total_money for raise_size in raise_sizes]

    match action:
        case 9:
            player.fold()
        case 8:
            player.check()
        case 7: 
            player.call(table.current_raise)
        case _:
            player._raise(raise_amounts[action])

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
def is_legal_action():
    pass

if __name__ == "__main__":
    num_players = 8
    num_state_variables = 20
    num_outputs = 10

    player_networks = []
    for _ in range(num_players):
        network = simple_dqn(num_state_variables, num_outputs)
        player_networks.append(network)

    buildTable(num_players)

    first_action = True
    memory_buffers = [ReplayBuffer(5000) for _ in range(num_players)]
    while table.has_a_player_raised() or first_action:
        
        first_action = False
        for player_ind in range(len(player_networks)):
            player_network = player_networks[player_ind]
            player = players[player_ind]

            state = table.get_state()

            q_values = player_network.get_model_output(state)
            current_max = q_values[0]

            max_index = 0
            for val_index in range(len(q_values)):
                new_max = max(current_max, q_values[val_index])
                if new_max != current_max:
                    max_index = val_index
                    current_max = new_max
            
            
            action(player, max_index)

            next_state = table.get_state()

            memory = Memory(state, max_index, 0, next_state, table.hand_done)
            memory_buffers[player_ind] = memory

        for memory_buffer in memory_buffers:
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
    