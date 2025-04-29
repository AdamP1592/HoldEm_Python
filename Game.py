from game.Table import Table

from game.Logger import Logger
from dqn import *

from GameTests import *

import random

l = Logger(reset=True)
Logger.is_logging = False

table = Table()
players = []

base_reward_weights = {"win": 1, "fold": 1}

reward_weights = {}

table_rewards = {}

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

def get_active_players(starting_player_key):
    print("Building active player queue")
    players_to_move = []
    player_keys = list(table.players.keys())

    starting_player_index = player_keys.index(starting_player_key)

    for player_index in range(len(table.players)):
        current_index = (starting_player_index + player_index) % (len(table.players))
        current_player_key = player_keys[current_index]
        player = table.players[current_player_key]

        print(f"Seat:{current_index}, folded:{player.folded}, raise:{player.total_bet}, current_raise:{table.current_raise} {'in' if not player.folded else 'out'}")
        if not player.folded:
            players_to_move.append( (current_player_key, player, current_index))
    
    return players_to_move

def play_hand_v2(player_models):
    starting_money = {}

    for player_key in table.players:
        starting_money[player_key] = table.players[player_key].total_money

    table.apply_blind()
    table.update_pot()
    table.deal()
    
    memory_buffers = [ReplayBuffer(8000) for _ in range(len(table.players))]
    negative_memory_buffers = [ReplayBuffer(300) for _ in range(len(table.players))]
    num_actions = [0 for _ in range(len(table.players))]


    l.log("Starting New Hand: \n")
    l.log("Starting Table Information: ")
    l.log("Table Stage " + table.current_stage)
    l.log("Starting Raise: " + str(table.current_raise))
    l.log("Pot: " + str(table.pot))
    l.log("Starting Player: " + str(table.get_starting_player()))

    for player_key in table.players:
        player = table.players[player_key]
        l.log("Player" + str(player_key))
        l.log("Folded: " + str(player.folded))
        l.log("Raised: " + str(player.raised))
        l.log("Checked: " + str(player.checked))
        l.log("Money: " + str(player.total_money))
        l.log("Bet: " + str(player.total_bet))

    starting_player_key = table.get_starting_player()
    break_case = False
    pre_flop = True
    pre_flop_passed = False
    
    while (table.current_stage != "pre-flop" or pre_flop) and not break_case:
        pre_flop = False
        print("Start of round: ", table.current_stage)
        if table.current_stage == "flop":
            pre_flop_passed = True

        

        player_move_queue = get_active_players(starting_player_key)
        print("Number of active players: ", len(player_move_queue))
        if len(player_move_queue) <= 1:
            continue
        
        while player_move_queue and not break_case:
            for player_key, player, network_index in player_move_queue:
                print(network_index, end = " ")

            
            print()
            current_player_key, current_player, network_index = player_move_queue.pop(0)

            print(network_index, end=": ")
            current_player.print_hand()

            
            print("Community Cards:")
            table.print_comm_cards()
            print("Current Raise: ", table.current_raise)

            for player_key in table.players:
                current_player_bet = table.players[player_key].total_bet
                if table.players[player_key].folded:
                    print("Folded", end = " ")
                    continue
                elif player_key == current_player_key:
                    print("*", end="")
                print(current_player_bet, end=" ")
            


            table_state = table.get_state(current_player_key)
            player_action = player_models[network_index].forward(table_state)

            while not break_case:
                if is_legal_action(player_action, current_player_key):
                    action(current_player, player_action)    
                    print("Action: ", player_action)
                    new_state = table.get_state(current_player_key)
                                        
                    if current_player.folded:
                        live_seats = sum([1 for p in table.players.values() if not p.folded])
                        if live_seats <= 1:
                            break_case = True

                    elif current_player.raised:
                        player_move_queue = get_active_players(current_player_key)
                        starting_player_key = current_player_key
                        if player_move_queue:
                            player_move_queue.pop(0)


                    mem = Memory(table_state, player_action, 0, new_state, False)
                    memory_buffers[network_index].store_memory(mem)
                    num_actions[network_index] += 1
                    break

                else:

                    mem = Memory(table_state, player_action, -1.0, table_state, False)
                    negative_memory_buffers[network_index].store_memory(mem)

                    player_action = player_models[network_index].forward(table_state, epsilon=1.0)

            if len(negative_memory_buffers[network_index]) > 50:
                memories = negative_memory_buffers[network_index].sample(10)
                player_models[network_index].batch_train_memories(memories)
        print("End of betting round")
        table.advance_stage()

    print(table.current_stage, " ", pre_flop_passed)
    if table.current_stage != "pre-flop" or not pre_flop_passed:
        table.reset_hand()
    print("\n\n****HAND OVER****\n\n")

    
    rewards = get_rewards_with_weights(starting_money)

    player_keys = list(rewards.keys())

    gamma = 0.95
    print(num_actions)
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
            memory_buffer.merge_buffers(negative_memory_buffers[player_key_index])
            
    
    return memory_buffers

def get_rewards(starting_money:dict):

    prev_winners = table.get_prev_winner() # those that won
    rewards = {}

    percent_change_in_money = {}

    for player_key in table.players:
        #amount won relative to the base hand size
        percent_change = (table.players[player_key].total_money - starting_money[player_key]) / (starting_money[player_key])
        # win amount takes up half the weight. Whether or not the player gained any money at all takes up the other half
        rewards[player_key] = (percent_change * 0.1) + (0.75 * ( 2 * ( int(percent_change > 0)) - 1 ) ) 
        #punishment for folding
        rewards[player_key] += int(table.players[player_key].folded) * -0.1
        percent_change_in_money[player_key] = percent_change
    #normalizes reward to (-1.0, 1.0)
    max_reward = max(abs(x) for x in rewards.values())
    for player_key in rewards:
        rewards[player_key] /= max_reward
    print(rewards)
    return rewards

def get_rewards_with_weights(starting_money:dict):
    rewards = {}
    percent_change_in_money = {}
    
    
    for player_key in table.players:
        target_reward_weights = reward_weights[player_key]

        win_weight = target_reward_weights[0]
        fold_weight = target_reward_weights[1]
        #amount won relative to the base hand size
        percent_change = (table.players[player_key].total_money - starting_money[player_key]) / (starting_money[player_key])
        # win amount takes up half the weight. Whether or not the player gained any money at all takes up the other half
        rewards[player_key] = (percent_change * (1 - win_weight)) + (win_weight * ( 2 * ( int(percent_change > 0)) - 1 ) ) 
        #punishment for folding
        rewards[player_key] += int(table.players[player_key].folded) * (- fold_weight)
        percent_change_in_money[player_key] = percent_change
    #normalizes reward to (-1.0, 1.0)
    max_reward = max(abs(x) for x in rewards.values())
    for player_key in rewards:
        rewards[player_key] /= max_reward
    print(rewards)

    return rewards

def get_new_weights(old_keys):
    average_weights = [0 for i in range(len(base_reward_weights))]
    for player_key in old_keys:
        
        for index in range(len(base_reward_weights)):
            average_weights[index] += reward_weights[player_key][index]

    average_weights = [w/(len(old_keys)) for w in average_weights]

    new_weights = [ [] for i in range(len(old_keys))]
    for index in range(len(new_weights)):
        changed_weights = average_weights[:] # clone of averages

        random_index = random.randint(0, len(base_reward_weights) - 1)
        random_modification = random.uniform(0.9, 1.05)

        changed_weights[random_index] *= random_modification
        new_weights[index] = changed_weights
    return new_weights

def update_low_performers(sorted_losses):
    num_players = len(sorted_losses)
    keys = list(sorted_losses.keys())

    first_two = keys[:2]
    next_two = keys[2:4]
    
    new_weights = []
    new_weights += get_new_weights(first_two)
    new_weights += get_new_weights(next_two)
    
    #average the weights, generate two new weights with a
    #random modification to each of the new weights

    print("New Weights: ")
    for index in range(num_players - 1, (num_players - 1)//2, -1):# 7 -> 3
        print(index)
        key = keys[index] # 7, 6, 5, 4
        offset = (num_players - 1) - index

        print(f"Player: {key}, Loss Count: {sorted_losses[key]} Old Weights: {reward_weights[key]}, New Weights: {new_weights[offset]}")
        reward_weights[key] = new_weights[offset]# 0, 1, 2, 3

    for player_key in sorted_losses:
        print(f"Player: {player_key}, Loss Count: {num_losses[player_key]}")

if __name__ == "__main__":
    num_players = 8

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

    num_episodes = 1000

    num_generations = 20

    player_networks = []


    num_losses = {}

    build_table(num_players)

    cumulative_memories = [ReplayBuffer(8000) for _ in range(num_players)]


    for player_key in table.players:
        win_weight = random.random()
        fold_weight = random.random()
        reward_weights[player_key] = [win_weight, fold_weight]
        num_losses[player_key] = 0
    print(reward_weights)

    #enerates all the networks
    for _ in range(num_players):
        network = simple_dqn(num_state_variables, num_outputs)
        player_networks.append(network)

    for gen in range(num_generations):
        for eps in range(num_episodes):
            starting_money = [player.total_money for player in table.players.values()]
            memory_buffers = play_hand_v2(player_networks)
            
            for network_index in range(len(player_networks)):
                
                #folds the old memories into the new memories for training
                new_mem_sample_size = min(10, len(memory_buffers[network_index]))
                old_mem_sample_size = min(100, len(cumulative_memories[network_index]))
                
                memories = memory_buffers[network_index].sample(new_mem_sample_size)
                memories += cumulative_memories[network_index].sample(old_mem_sample_size)
                

                #grabs all the memories from the old hand
                if len(memories) > 1:
                    player_networks[network_index].batch_train_memories(memories)
                    cumulative_memories[network_index].merge_buffers(memory_buffers[network_index])

            #resets each player
            for index, key in enumerate(table.players):
                player = table.players[key]
                starting_balance = starting_money[index]

                if player.total_money < starting_balance:
                    num_losses[key] += 1

                player.total_money = 5000
            
            print(table.game.deck.size)
        next_weights = {}

        #top 2 make 2 children
        #next 2 make 2 children

        sorted_losses = {k: v for k, v in sorted(num_losses.items(), key=lambda item: item[1])}
        update_low_performers(sorted_losses)
                
        for key in num_losses:
            num_losses[key] = 0
