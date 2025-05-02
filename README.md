# Genetic Reward-Shaped Dueling Dobule Deep Q-Network


## Project Summary

A reinforcement learning framework for training poker-playing agents using a Generational Genetic Evolution strategy that evolves reward functions rather than policies. The system employs Dueling Double Deep Q-Networks with Huber loss, Adam optimization, and retroactive reward shaping to promote the discovery of robust, generalizable reward strategies across fresh network instantiations.


**Recommended minimum DRAM to run the training loop**: 16 gb. If you train with less ram, reduce the replay buffer, cumulative replay buffer size, and network size. The current version takes somewhere between 8 and 10 gigs(about 1 gig per network) due to the memory storage and tensorflow graph storage due to calling tf.function() on the unwrapped training loop. E

## Network

This project implements a Generational Genetic Evolutionary Deep Reinforcement Learning framework for optimizing agent behavior in a competitive card game environment that primarly leverages TensorFlow's underlying framework and Numpy.
Rather than directly evolving neural network weights, the algorithm evolves reward shaping strategies over generations, ensuring fair competition and reducing momentum bias.

At the beginning of each generation, a fresh population of neural networks is initialized.
Each network is trained over many episodes using a Dueling Double DQN architecture, leveraging Huber loss for stable learning and Adam optimization for adaptive gradient descent.

After all episodes in a generation:

- Player performance is ranked based on a cumulative loss metric (e.g., number of hands lost).

- Top performers' reward strategies are averaged and mutated slightly to create new reward schemes.

- Lowest-performing players adopt these new mutated reward functions.

- Neural networks are reset (fresh randomized weights) for the next generation, ensuring no cross-generation bias.

Replay buffers accumulate experience within a generation and are flushed between generations to prevent stale learning across resets.
A retroactive reward adjustment scheme is used during training, where the reward is distributed backward across actions, discounted by the timestep.

The system promotes the discovery of robust reward shaping strategies that generalize across networks rather than overfitting to a specific training history.

## HoldEm

### Core Compnents:

#### Card:

Encodes suit, face value, and optional high-value (e.g., Ace as 14). Each card includes a normalized ID for one-hot encoding.

#### Deck:

Supports multiple decks, random shuffling, card dealing, and recycling.

#### Hand:

Encapsulates a player’s hole cards. Includes utilities to hide/show cards, print hands, and compute temporary values.

#### Player:

- Current hand, total money, total bet, and raise amount
- Action Methods: call(), raise_(), check(), and fold()
- reset() is called at the end of a hand to reset everything
- next_turn() is called at the end of a betting round

#### HandRanker

- rank_players(...) takes in a list of the community cards(cards in the hole) and a dict of {player_key: hand_object}. returns full poker hand ranks.

#### Table

This is an interface with the core game mechanics class HoldEm and RL interface with the game.
- Initalizes players.
- Defines betting stages.
- Rotates blinds, tracks current raise, and encodes game state for each agent.

#### HoldEm

This class drives the core game progression.
- Manages community cards, pot, and players
- Computes winners
- interfaces with HandRanker

### Main File

- Manages game loop.
- Initalizes N players(agents) each with a fresh Dueling Double DQN and Memory Buffer
- For each **generation**:
    - Networks are reset
    - Agents are trained over multiple episodes where each episode is a full poker hand
    - Cumulative Memory Buffer: Stores memories over every hand in a generation
- After training:
    - Players are ranked by performance
    - Poor performers reward vectors are replaced with mutated high performer reward vectors
    - Networks are reset
- Rewards are:
    - Shaped by two weights that apply to three rewards: 
        - win_weight: dictates the reward for winning the hand and the reward for the amount won for the hand
        - fold_weight: dictates the penalty for folding

### Future Work

- Multi-network approach per generation:
    - Every generation's rewards are ran through several networks to confirm generalization of reward scheme applies to every possible network

- Decay scheduling for learning rate an epsilon
- Refine dram usage for efficiency
