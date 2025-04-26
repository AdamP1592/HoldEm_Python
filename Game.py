from game.Table import Table
from dqn import *

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
    players.clear()
    for i in range(numPlayers):
        players.append(table.add_player())

def is_legal_action(action_index, player_key):
    player = table.players[player_key]
    
    if player.folded:
        return False

    match action_index:
        case 9:  #Fold
            return True
        case 8:  #Check
            return table.current_raise == player.raise_amount or player.total_money == 0
        case 7:  #Call
            return table.current_raise > player.raise_amount
        case 6:  #All-in
            return player.total_money > 0  # Can only go all-in if you have chips
        case _:  #Raise
            if player.total_money == 0:
                #cant raise if you have no money.
                return False

            raise_amount = 0
            if table.current_stage == "pre-flop":
                table.current_raise += table.get_blind(player_key)
            raise_amount += raise_sizes[action_index] * player.total_money

            return raise_amount > table.current_raise and raise_amount < player.total_money

    return False
def play_hand(player_models):
    table.apply_blind()
    table.update_pot()
    starting_money = {}

    for player_key in table.players:
        starting_money[player_key] = table.players[player_key].total_money

    player_key_list = list(table.players.keys())
    starting_player_key = table.get_starting_player()

    round_end_ind = player_key_list.index(starting_player_key)

    memory_buffers = [ReplayBuffer(8000) for _ in range(len(table.players))]
    negative_memory_buffers = [ReplayBuffer(300) for _ in range(len(table.players))]

    pre_flop = True # to ensure the current hand is the inital pre-flop
    break_case = False
    print(table.current_stage)
    
    while (table.current_stage != "pre-flop" or pre_flop) and not break_case:
        print(table.current_stage)
        if table.current_stage == "flop":
            print("Dealing")
            table.deal()

        pre_flop = False
         
        i = 0
        #iterate over the length of the players.
        #if a player raises, shift round_end_ind to the current index and then
        #reset i to 0
        while i < len(player_models):
            current_player_index = (round_end_ind + i) % len(player_models)
            current_player_key = player_key_list[current_player_index]
            current_player = table.players[current_player_key]
            #skip player if he has folded
            if current_player.folded:
                i+=1
                continue

            table_state = table.get_state(current_player_key)
            #check if there is only one active player they win
            active_players = [p_key for p_key, p in table.players.items() if not p.folded]
            if len(active_players) != 1:
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
                if current_player.get_hand():
                    current_player.print_hand()

                print("Actions:\n\t0-6 raise\n\t7:Call\n\t8:check\n\t9:fold")
                print("Table State:", len(table_state))
                player_action = player_models[current_player_index].forward(table_state)
                while True:
                    if is_legal_action(player_action, current_player_key):
                        print(table.players[current_player_key])
                        print(player_action)
                        action(table.players[current_player_key], player_action)
                        new_state = table.get_state(current_player_key)
                        if player_action < 7 and player_action >= 0:
                            i = 0
                            round_end_ind = current_player_index + 1
                        else:
                            i+=1
                        mem = Memory(table_state, player_action, 0, new_state, False)
                        #reward will only be assigned after the hand is done
                        #if the player wins, then all memories stored will be 
                        memory_buffers[current_player_index].store_memory(mem)
                        break
                    else:
                        mem = Memory(table_state, player_action, -1.0, table_state, False)
                        negative_memory_buffers[current_player_index].store_memory(mem)
                        #if action taken is invalid choose a random aciton with egreedy
                        player_action = player_models[current_player_index].forward(table_state, 1.0)
                if len(negative_memory_buffers[current_player_index]) > 50: 
                    memories = negative_memory_buffers[current_player_index].sample(10)
                    player_models[current_player_index].batch_train_memories(memories)
            else:
                break_case = True
                break
        if not break_case:
            table.advance_stage()

    for pk in table.players:
        print(table.players[pk].folded, table.current_stage)

    if table.current_stage != "pre-flop":# catch case if the hand ended before a reset
        table.reset_hand()

    rewards = get_rewards(starting_money)

    player_keys = list(rewards.keys())

    gamma = 0.95

    for player_key_index in range(len(player_keys)):
        
        player_key = player_keys[player_key_index]
        player = table.players[player_key]
        memory_buffer = memory_buffers[player_key_index]

        for memory_ind in range(len(memory_buffer.buffer)):
            memory = memory_buffer.buffer[memory_ind]
            
            #reward gets distributed with diminishing reward 
            #across each move
            memory.reward = rewards[player_key] * (gamma ** memory_ind)

        if memory_buffer.buffer:
            memory_buffer.buffer[-1].is_done = True
            memory_buffer.merge_percentage_of_self(negative_memory_buffers[player_key_index], 0.05)

    return memory_buffers



def get_rewards(starting_money:dict):

    prev_winners = table.get_prev_winner() # those that won
    rewards = {}

    percent_change_in_money = {}

    for player_key in table.players:
        #amount won relative to the base hand size
        percent_change = (table.players[player_key].total_money - starting_money[player_key]) / (starting_money[player_key])
        rewards[player_key] = percent_change
        #punishment for folding
        rewards[player_key] += int(table.players[player_key].folded) * -0.02

        percent_change_in_money[player_key] = percent_change

    for winner_key in prev_winners:
        rewards[winner_key] += 0.1 * abs(rewards[winner_key])
        # multiplies the reward by the absolute value of the percent change

    #normalizes reward to (-1.0, 1.0)
    max_reward = max(abs(x) for x in rewards.values())
    for player_key in rewards:
        rewards[player_key] /= max_reward

    return rewards


if __name__ == "__main__":
    num_players = 3

    # State encoding:
    # 52 one-hot for hole cards
    # 52 one-hot for community cards
    # +1 pot / base_money
    # +1 starting player index / num_players
    # +1 your index / num_players
    # +1 your total_money / base_money
    # +1 current raise / base_money
    # +4 one-hot for betting stage (preflop, flop, turn, river)
    # +3 * num_players for each player:
    #     - 1 if folded (0 or 1)
    #     - 1 total bet / base_money
    #     - 1 raise amount / base_money


    num_state_variables = 113 + (num_players * 4)

    num_outputs = 10

    num_episodes = 100

    player_networks = []


    num_losses = [0 for _ in range(num_players)]

    build_table(num_players)

    #enerates all the networks
    for _ in range(num_players):
        network = simple_dqn(num_state_variables, num_outputs)
        player_networks.append(network)

    for eps in range(num_episodes):
        starting_money = [player.total_money for player in table.players.values()]
        memory_buffers = play_hand(player_networks)

        for network_index in range(len(player_networks)):
            sample_size = min(100, len(memory_buffers[network_index]))
            memories = memory_buffers[network_index].sample(sample_size)
            player_networks[network_index].batch_train_memories(memories)

        #resets each player
        for index, key in enumerate(table.players):
            player = table.players[key]
            starting_balance = starting_money[index]

            if player.total_money < starting_balance:
                num_losses[index] += 1

            player.total_money = 5000
        print(table.game.deck.size)
    for loss_count in num_losses:
        print(loss_count)
    
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