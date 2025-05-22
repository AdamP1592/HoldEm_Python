from game.Table import Table

from game.Logger import Logger
from dqn import *

from GameTests import *

import random, ast, os
import math
import keyboard

l = Logger(reset=True)
Logger.is_logging = False

table = Table()
players = []
average_number_of_actions = []

base_reward_weights = {"win": 1, "fold": 1, "bust": 1, "money gained": 1}

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

raise_sizes = [0.01, 0.05, 0.1, 0.2, 0.5, 0.75, 1.0]

def action(player, action:int):
    #action = some int between 0 and 9

    raise_amounts = [raise_size * player.total_money for raise_size in raise_sizes]

    match action:
        case 9:
            player.fold()
        case 8:
            player.check()
        case 7: 
            if player.total_money < table.current_raise:
                player.all_in = True
            player.call(table.current_raise)
        case 6:
            raise_amount = player.total_money
            player.raise_(raise_amount)
            player.all_in = True
        case _:

            raise_amount = raise_amounts[action] + table.current_raise
            player.raise_(raise_amount)
                        
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
            raise_amount = raise_sizes[action_index] * player.total_money 

            return raise_amount > table.current_raise and raise_amount < player.total_money

    return False

def get_player_action() -> int:
    action_map = {
        0: "Raise 1%", 1: "Raise 5%", 2: "Raise 10%", 3: "Raise 20%", 
        4: "Raise 50%", 5: "Raise 75%", 6: "Raise 100%", 
        7: "Call", 8: "Check", 9: "Fold"
    }

    while True:
        print("\nChoose Action:")
        for k, v in action_map.items():
            print(f"{k}: {v}")
        try:
            choice = int(input("Enter action number: "))
            if 0 <= choice <= 9:
                return choice
            else:
                print("Invalid number. Must be 0–9.")
        except ValueError:
            print("Invalid input. Enter a number.")


def is_running_in_vscode():
    return 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'vscode'


def play_hand_against_models(player_models):
    starting_money = {}
    
    human_player_index = len(player_models) - 1
    human_player_key = list(table.players.keys())[human_player_index]

    #check if each player bust
    for player_key in table.players:
        starting_money[player_key] = table.players[player_key].total_money
        if table.players[player_key].total_money == 0:
            #if not table.players[player_key].bust == False:
            #    l.log(f"Player {str(player_key)} bust")
            table.players[player_key].bust = True
            
        #print(player_key)

    #apply blinds and deal cards
    table.apply_blind()
    table.update_pot()
    table.deal()

    """  DEBUG
    print("All player hands")
    for player in table.players.values():
        player.print_hand()
        l.log(player.get_hand_str())
    """

    # setup all loop flags
    hand_over = False
    pre_flop = True
    pre_flop_passed = False

    # generate folded players dict
    folded_players = {}
    for player_key in table.players:
        folded_players[player_key] = False

    # builds move queue
    player_keys = list(table.players.keys())
    big_blind_index = player_keys.index(table.big_blind_key)
    # player after the big blind goes first, big blind goes last
    starting_player_key = player_keys[(big_blind_index + 1) % len(player_keys)]

    player_move_queue = table.get_active_players(starting_player_key, starting_key_removal = False)
        
    while (table.current_stage != "pre-flop" or pre_flop) and not hand_over:
        pre_flop = False

        # prevents actions after the last player
        last_player = False

        #loops through active players
        while len(player_move_queue) != 0 and not hand_over and not last_player:

            current_player_key, current_player, network_index = player_move_queue.pop(0)
            ### DEBUG ###
            l.log("Table Current Raise: " + str(table.current_raise))
            l.log("Player: " + str(current_player_key))
            l.log("Money: " + str(current_player.total_money))
            l.log("Total Bet: " + str(current_player.total_bet))
            l.log("Current Raise: " + str(current_player.raise_amount))

            table_state = table.get_state(current_player_key)

            #gets the inital action for the current player
            table.print_table_state(current_player_key = current_player_key,human_player_key = human_player_key)
            player_action = None
            if network_index != human_player_index:
                player_action = player_models[network_index].forward(table_state)
            else:
                
                player_action = get_player_action()
            
                
            bad_action_count = 0
            action_loop_over = False

            #loops repeatdly until action is taken. If the hand is over as a result
            # break all loops
            while not (hand_over or action_loop_over):
                #if the action is legal, perform action, rebuild betting queue,
                #and set the starting player for the next stage to
                if is_legal_action(player_action, current_player_key):
                    #print(player_action)
                    print(player_action)
                    action(current_player, player_action)
                    
                    # if they fold check if there are any more live seats, if there are none the hand is over
                    if current_player.folded:
                        #print("Current Player Folded")
                        folded_players[current_player_key] = True
                        live_seats = sum([1 for p in table.players.values() if not p.folded or p.bust or p.all_in])
                        if live_seats <= 1:
                            hand_over = True
                    # if the player raised, rebuild the action queue, if there is only
                    # one player in the new queue, there is one or fewer players in the
                    # queue then the current player is the last player in the hand
                    elif current_player.raised:

                        player_move_queue = table.get_active_players(current_player_key, starting_key_removal = True)

                        # ensure the current player isn't the last player in the hand
                        # if he's the last to move then  
                        if len(player_move_queue) > 1:
                            last_player = False
                        # move the starting player key to the last person that raised
                        # for the next betting round
                        starting_player_key = current_player_key
                    #print(hand_over)
                    action_loop_over = True

                # if its an illegal action, redo the action
                else:
                    if network_index != human_player_index:
                        #print("Illegal action: ", player_action)
                        player_action = player_models[network_index].forward(table_state, epsilon=1.0)
                        if bad_action_count >= 20:
                            input("Debug: press enter to continue")
                    else:
                        player_action = get_player_action()
                    bad_action_count += 1
        #print("end of betting round", hand_over, last_player, len(player_move_queue))
        #print("end of queue loop")
        print("End of betting round.")
        #print(table.current_stage)

        # end of first round
        pre_flop_passed = True

        # end of hand catch case
        if len(player_move_queue) <= 1:
            last_player = True
            #print("Last player to move")
        if not is_running_in_vscode():
            os.system("cls")
        # end of hand log and visual
        if table.current_stage == "river" or last_player:
            l.log("Final Pot: " + str(table.pot))
            print("Final Pot: ", table.pot)
            table.print_table_state(display_hands=True)
        
        table.advance_stage()
        player_move_queue = table.get_active_players(starting_player_key, starting_key_removal = False)

    # if the hand didn't fully conclude reset it
    if table.current_stage != "pre-flop" or not pre_flop_passed:
        table.reset_hand()

    # display winnings
    print("Player Balances: ")
    for index, key in enumerate(table.players):
        player = table.players[key]
        balance_string = f"Player P{index}: ${player.total_money:.2f} {'(You)' if key == human_player_key else ''}"
        l.log(balance_string)
        print(balance_string)
    #print(table.current_stage, " ", pre_flop_passed)

    print("\n\n****HAND OVER****\n\n")

def play_hand_v2(player_models):
    starting_money = {}

    for player_key in table.players:
        starting_money[player_key] = table.players[player_key].total_money

    table.apply_blind()
    table.update_pot()
    table.deal()
    
    memory_buffers = [ReplayBuffer(500) for _ in range(len(table.players))]
    negative_memory_buffers = [ReplayBuffer(100) for _ in range(len(table.players))]
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

    starting_player_key = table.big_blind_key

    hand_over = False
    pre_flop = True
    pre_flop_passed = False

    folded_players = {}
    for player_key in table.players:
        folded_players[player_key] = False

    # builds move queue
    player_keys = list(table.players.keys())
    big_blind_index = player_keys.index(table.big_blind_key)
    # player after the big blind goes first, big blind goes last
    starting_player_key = player_keys[(big_blind_index + 1) % len(player_keys)]

    player_move_queue = table.get_active_players(starting_player_key, starting_key_removal = False)
        
    while (table.current_stage != "pre-flop" or pre_flop) and not hand_over:

        pre_flop = False
        #generate player move queue

        # prevents actions after the last player
        last_player = False

        #loops through active players
        while len(player_move_queue) != 0 and not hand_over and not last_player:
            #prints all players information in the queue
            for player_key, player, network_index in player_move_queue:
                print(network_index, end = " ")
            print()
            current_player_key, current_player, network_index = player_move_queue.pop(0)

            #prints the index of the current player's network
            print(network_index, end=": ")
            #prints hand of player
            current_player.print_hand()
            
            #prints all comm cards
            print("Community Cards:")
            table.print_comm_cards()
            print("Current Raise: ", table.current_raise)

            # prints all player raises and which is the current player to move
            for player_key in table.players:
                current_player_bet = table.players[player_key].total_bet
                if table.players[player_key].folded:
                    print("Folded", end = " ")
                    continue
                elif player_key == current_player_key:
                    print("*", end="")
                print(current_player_bet, end=" ")
            
            #gets current table state
            table_state = table.get_state(current_player_key)

            #gets the action
            player_action = player_models[network_index].forward(table_state)
            action_loop_over = False
            #loops until valid action is recieved
            while not (hand_over or action_loop_over):
                # if there is a legal action, perform action,
                if is_legal_action(player_action, current_player_key):
                    action(current_player, player_action)    
                    print("Action: ", player_action)
                    new_state = table.get_state(current_player_key)
                                        
                    if current_player.folded:
                        folded_players[current_player_key] = True
                        live_seats = sum([1 for p in table.players.values() if not p.folded])
                        if live_seats <= 1:
                            hand_over = True

                    elif current_player.raised:
                        player_move_queue = table.get_active_players(current_player_key, starting_key_removal = True)

                        # ensure the current player isn't the last player in the hand
                        # if he's the last to move then  
                        if len(player_move_queue) > 1:
                            last_player = False
                        # move the starting player key to the last person that raised
                        # for the next betting round
                        starting_player_key = current_player_key

                    # Generate a new memory for the action with an empty reward value
                    # Reward will be set based on hand result.
                    mem = Memory(table_state, player_action, 0, new_state, False)
                    memory_buffers[network_index].store_memory(mem)
                    num_actions[network_index] += 1

                    #end action loop because there was a valid action
                    action_loop_over = True

                else:
                    #generate new memory for the bad actions
                    mem = Memory(table_state, player_action, -1.0, table_state, False)
                    negative_memory_buffers[network_index].store_memory(mem)

                    # generate a completely random action
                    player_action = player_models[network_index].forward(table_state, epsilon=1.0)
            # if a ton of bad actions are made, force the network to learn to not do that
            if len(negative_memory_buffers[network_index]) > 50:
                memories = negative_memory_buffers[network_index].sample(10)
                player_models[network_index].batch_train_memories(memories)

        print("End of betting round")

        # end of first round
        pre_flop_passed = True

        # end of hand catch case
        if len(player_move_queue) <= 1:
            last_player = True
            print("Last player to move")

        # end of hand log and visual
        if table.current_stage == "river" or last_player:
            l.log("Final Pot: " + str(table.pot))
            print("Final Pot: ", table.pot)
        
        table.advance_stage()
        player_move_queue = table.get_active_players(starting_player_key, starting_key_removal = False)



    print(table.current_stage, " ", pre_flop_passed)
    if table.current_stage != "pre-flop" or not pre_flop_passed:
        table.reset_hand()
    print("\n\n****HAND OVER****\n\n")

    
    rewards = get_rewards_with_weights(starting_money, folded_players)

    player_keys = list(rewards.keys())

    gamma = 0.95
    print(num_actions)
    for player_key_index in range(len(player_keys)):
        average_number_of_actions[player_key_index] += num_actions[player_key_index]
        
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
            
    
    return (memory_buffers, folded_players, num_actions)

def interpolate_reward(min_reward, max_reward, raw_reward):
    if abs(max_reward - min_reward) < 1e-6:
        return 0.0
    return ((raw_reward - min_reward) / (max_reward - min_reward) * 2) - 1


def get_rewards_with_weights(starting_money:dict, folded_players:dict):
    rewards = {}
    percent_change_in_money = {}
    
    # Rewards:
    # Player gained money
    # The percent change in money
    # The player bust
    # The player folded

    for player_key in table.players:


        target_reward_weights = reward_weights[player_key]

        print("Total Money: ", table.players[player_key].total_money, "Folded: ", folded_players[player_key])
        print("Weights: ", target_reward_weights)

        win_weight = target_reward_weights[0]
        fold_weight = target_reward_weights[1]
        bust_weight = target_reward_weights[2]
        money_gained_weight = target_reward_weights[3]
        #amount won relative to the base hand size
        percent_change = (table.players[player_key].total_money - starting_money[player_key]) / (starting_money[player_key])

        #clips the percent change for overwhelming victories because that skews every players reward too far
        if percent_change > 1:
            percent_change = 1.0 + 0.25 * math.tanh((percent_change - 1.0) * 2)

        win_reward = (win_weight * ( int(percent_change > 0)) ) 
        percent_change_reward = (percent_change * money_gained_weight) 
        fold_punishment = int(folded_players[player_key]) * (- fold_weight) * 1.25
        bust_punishment = - bust_weight * int(table.players[player_key].total_money == 0)

        #gets the base reward with each generations weight vector for rewards
        raw_reward = win_reward + percent_change_reward + fold_punishment + bust_punishment
        #normalizes the rewards based on the highest possible and lowest possible reward
        max_possible_reward = (1.25 * money_gained_weight) + win_weight
        min_possible_reward = - (money_gained_weight + (1.25 * fold_weight) + bust_weight)

        reward = interpolate_reward(min_possible_reward, max_possible_reward, raw_reward)
        assert -1.0 <= reward <= 1.0, f"reward out of bounds: {reward}"
        
        #applies reward
        rewards[player_key] = reward

        #for debugging
        #percent_change_in_money[player_key] = percent_change
        #print(f"Total Reward: {rewards[player_key]}, Win Reward: {win_reward}, Percent change in money reward: {percent_change_reward}, Fold Punishment: {fold_punishment}, Bust Punishment: {bust_punishment}")

    print(rewards)

    return rewards

def get_new_weights(old_keys, mean_shift = 0.0, modification_range = 0.25):
    average_weights = [0 for i in range(len(base_reward_weights))]
    for player_key in old_keys:
        
        for index in range(len(base_reward_weights)):
            average_weights[index] += reward_weights[player_key][index]

    average_weights = [w/(len(old_keys)) for w in average_weights]

    new_weights = [ [] for i in range(len(old_keys))]
    for index in range(len(new_weights)):
        changed_weights = average_weights[:] # clone of averages

        random_index = random.randint(0, len(base_reward_weights) - 1)

        mean_modification = 1.0 + mean_shift
        random_modification = random.uniform(mean_modification - (modification_range/2),
                                            mean_modification + (modification_range/2))

        changed_weights[random_index] *= random_modification
        new_weights[index] = changed_weights
    return new_weights

def update_low_performers(sorted_losses):
    num_players = len(sorted_losses)
    keys = list(sorted_losses.keys())

    first_two = keys[:2]
    next_two = keys[2:4]
    
    new_weights = []
    new_weights += get_new_weights(first_two, modification_range = 0.1)
    new_weights += get_new_weights(next_two, modification_range = 0.5)
    
    #average the weights, generate two new weights with a
    #random modification to each of the new weights

    print("New Weights: ")
    for index in range(num_players - 1, (num_players - 1)//2, -1):# 7 -> 3
        print(index)
        key = keys[index] # 7, 6, 5, 4
        offset = (num_players - 1) - index

        print(f"Player: {key}, Loss Count: {sorted_losses[key]} Old Weights: {reward_weights[key]}, New Weights: {new_weights[offset]}")
        reward_weights[key] = new_weights[offset]# 0, 1, 2, 3

    
def train(num_players:int):
    global average_number_of_actions
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

    base_num_episodes = 1000

    num_generations = 35

    base_money = 5000

    player_networks = []


    failures = {}

    build_table(num_players)

    #generates random weight vector for each reward
    for player_key in table.players:
        reward_weights[player_key] = []
        for _ in range(len(base_reward_weights)):
            weight = random.random()
            reward_weights[player_key].append(weight)

        #sets the base money and failure count
        table.players[player_key].total_money = base_money
        failures[player_key] = 0

    print(reward_weights)

    num_episodes = base_num_episodes
    average_number_of_actions.clear()
    #Generates all the networks
    for index in range(num_players):
        network = simple_dqn(num_state_variables, num_outputs, num_episodes = num_episodes)
        player_networks.append(network)
        average_number_of_actions.append(0)
    
    #generation loop where each weight to the reward scheme is attempted
    for gen in range(num_generations):
        average_number_of_actions = [0 for _ in range(num_players)]
        #truncates gen/5 so if 1-1.999... modifier = 1 * 500
        num_episodes_modifier = (500 * int((gen//5) - 2 )) * int(gen >= 15)
        # after 14 episodes push the base number of episodes to 
        num_episodes = base_num_episodes + num_episodes_modifier
            
        #resets each network for every genration to get a generalizable reward scheme that optimizes performance
        for net in player_networks:
            net.reset()

        #generates memory buffers for each generation
        cumulative_memories = [ReplayBuffer(3000) for _ in range(num_players)]

        #episode loop
        for eps in range(num_episodes):
            
            print(gen)
            if keyboard.is_pressed('p'):
                input("Paused. Press Enter to resume.")
            starting_money = {}
            for key in table.players:
                starting_money[key] = table.players[key].total_money 

            #grabs useful data from the hands
            memory_buffers, folded_players, num_actions = play_hand_v2(player_networks)
            
            #folds the old memories into the new memories for training
            for network_index in range(len(player_networks)):
                
               
                new_mem_sample_size = min(10, len(memory_buffers[network_index]))
                old_mem_sample_size = min(100, len(cumulative_memories[network_index]))

                memories = (memory_buffers[network_index].sample(new_mem_sample_size) + 
                            cumulative_memories[network_index].sample(old_mem_sample_size))
                

                #grabs all the memories from the old hand
                if len(memories) > 0:
                    player_networks[network_index].batch_train_memories(memories)
                    cumulative_memories[network_index].merge_buffers(memory_buffers[network_index])

            #resets each player and builds out failure dict
                player = table.players[key]
                starting_balance = starting_money[key]

                #double failure if the player runs out of money
                if player.total_money <= starting_balance:
                    failures[key] += 1
                
                #resets player if they bust and adds a harsh punishment
                if player.total_money < 1:
                    failures[key] += 2
                    player.total_money = base_money

                #rapidly reduces money gained(to prevent lucky runs from giving too much) and gives a moderate reward for gaining money
                if player.total_money > base_money * 1.5:
                    player.total_money *= 0.7
                    failures[key] -= 0.5 # moderate reward for gaining money
                

            for key in folded_players:
                if folded_players[key]:
                    failures[key] += 0.5 #moderate punishment for folding
            print(eps)
            print(f"Generation: {gen}")
        
        #gets average of number of actions
        average_number_of_actions = [num_act/num_episodes for num_act in average_number_of_actions]

        

        #top 2 make 2 children
        #next 2 make 2 children
        # drop bottom 4

        sorted_losses = {k: v for k, v in sorted(failures.items(), key=lambda item: item[1])}
        update_low_performers(sorted_losses)
                
        for key in failures:
            failures[key] = 0
        for player in table.players.values():
            player.total_money = base_money

        #store networks every generation
        for model_ind in range(len(player_networks)):
            model_obj = player_networks[model_ind]
            model_obj.store_models(f"./networks/model{model_ind}/")

        with open("./networks/reward_weights.data", "w+") as f:
            for reward_scheme in reward_weights.values():
                f.write("Weights:  " + str(reward_scheme) + "\n")

def get_stored_reward_weights() -> list:
    loaded_weights = []
    with open("./networks/reward_weights.data", "r") as f:
        lines = f.readlines()
        
        for line in lines:
            # removes the "Weights: " from the file, then strips whitespace 
            weight_str = line.split("Weights:")[1].strip()
            weights = ast.literal_eval(weight_str)
            loaded_weights.append(weights)
    return loaded_weights

def get_stored_networks(num_players:int) -> list:
    networks = []
    for i in range(num_players):
        folder_path = f"./networks/model{i}/"
        network = simple_dqn.from_storage(folder_path)
        networks.append(network)
    return networks

def train_from_files(num_models):
    global reward_weights
    global average_number_of_actions

    weights = get_stored_reward_weights()

    if len(weights) != num_models:
        raise ValueError(f"Expected {num_models} weight sets, found {len(weights)}")

    
    num_episodes = 6000
    base_money = 5000

    player_networks = []

    reward_weights.clear()
    average_number_of_actions.clear()
    #sets reward weight vectors, clears
    build_table(num_models)
    
    
    for index, player_key in enumerate(table.players.keys()):

        reward_weights[player_key] = weights[index]
        table.players[player_key].total_money = base_money
        average_number_of_actions.append(0)

    player_networks = get_stored_networks(num_models)

    cumulative_memories = [ReplayBuffer(4000) for _ in range(num_models)]

    #episode loop
    for eps in range(num_episodes):
        if keyboard.is_pressed('p'):
            input("Paused. Press Enter to resume.")
        starting_money = {}
        for key in table.players:
            starting_money[key] = table.players[key].total_money 

        #grabs useful data from the hands
        memory_buffers, folded_players, num_actions = play_hand_v2(player_networks)
        
        #folds the old memories into the new memories for training
        for network_index in range(len(player_networks)):
            
            new_mem_sample_size = min(10, len(memory_buffers[network_index]))
            old_mem_sample_size = min(100, len(cumulative_memories[network_index]))

            memories = (memory_buffers[network_index].sample(new_mem_sample_size) + 
                        cumulative_memories[network_index].sample(old_mem_sample_size))
            

            #grabs all the memories from the old hand
            if len(memories) > 0:
                player_networks[network_index].batch_train_memories(memories)
                cumulative_memories[network_index].merge_buffers(memory_buffers[network_index])

        #resets each player and builds out failure dict
        for index, key in enumerate(table.players):
            player = table.players[key]
            
            #resets player if they bust and adds a harsh punishment
            if player.total_money < 1:
                player.total_money = base_money

            #rapidly reduces money gained(to prevent lucky runs from giving too much) and gives a moderate reward for gaining money
            if player.total_money > base_money * 1.5:
                player.total_money *= 0.7
    for model_ind in range(len(player_networks)):
        model_obj = player_networks[model_ind]
        model_obj.store_models(f"./networks/model{model_ind}/")

def play_against_models(total_num_models):
    global reward_weights
    global average_number_of_actions

    weights = get_stored_reward_weights()

    if len(weights) != total_num_models:
        raise ValueError(f"Expected {total_num_models} weight sets, found {len(weights)}")
    
    base_money = 5000

    player_networks = []

    reward_weights.clear()
    average_number_of_actions.clear()
    #sets reward weight vectors, clears
    build_table(total_num_models)
    
    
    for index, player_key in enumerate(table.players.keys()):
        reward_weights[player_key] = weights[index]
        table.players[player_key].total_money = base_money
        average_number_of_actions.append(0)

    player_networks = get_stored_networks(total_num_models)

    human_player_key = list(table.players.keys())[-1]
    passed_first_hand = False
    while table.players[human_player_key].total_money > 1:
        if passed_first_hand:
            choice = input("Press [Enter] to play next hand, or type 'q' to quit: ").lower()
            if choice == 'q':
                return
        play_hand_against_models(player_networks)
        passed_first_hand = True

def choose_operation(num_players=8):
    print("Options:\n1. Play against trained models\n2. Train stored networks\n3. Train new models")
    option = input("Enter the number of the option you would like.\n").strip()

    if "1" in option:
        play_against_models(num_players)
    elif "2" in option:
        train_from_files(num_players)
    elif "3" in option:
        confirmation = input("Training new models destroys existing models.\nAre you sure you want to train new models?(y/n)").strip().lower()
        if confirmation.contains("y"):
            train(num_players)
    else:
        print("Invalid input. Please try again.\n")
        choose_operation(num_players)
    
if __name__ == "__main__":
    num_players = 8
    #play_against_models(num_players)  
    choose_operation()
    #test_display()
    #test_rotating_blind_with_bust()
    print("EOF")
