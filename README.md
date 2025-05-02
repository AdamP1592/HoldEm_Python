# Genetic Reward-Shaped Dueling Double Deep Q-Network (G-D3QN)

## Overview

This project implements a reinforcement learning system for Texas Hold'em poker agents using a **generational genetic algorithm** that evolves **reward shaping vectors** rather than policies. It combines Dueling Double DQNs, a genetic strategy for optimizing reward weights, and environment-specific constraints designed for multi-agent competitive learning.

Agents are trained over **generations** using freshly initialized Dueling Double Deep Q-Networks. After each generation, networks are **discarded**, and only the **reward weight vectors** are evolved based on agent performance.

---

## Requirements

- Python 3.11 (minimum)
- TensorFlow 2.x
- NumPy

**Memory warning**: Full training consumes **8–10 GB RAM**. If using lower-spec hardware:
- Reduce network width/depth
- Decrease replay buffer sizes
- Swap from using tf.function in the dqn file to just the unwrapped function. Will yield slower training but will save a lot of ram

---

## Key Features

### Genetic Evolution of Reward Weights
- Each player has a **4-element reward weight vector** for:
  1. Win bonus
  2. Fold penalty
  3. Bust penalty
  4. Money gained multiplier
- Top-performing agents pass **mutated** versions of their reward vectors to weaker agents each generation.

### Dueling Double DQN Agents
- Each network outputs **advantage and value** streams, combined into Q-values.
- Uses:
  - **Huber Loss** for stability
  - **Adam optimizer**
  - **Target networks**
  - **Epsilon-greedy exploration**

### Retroactive Reward Shaping
- Rewards are assigned **after a hand ends**, not per-step.
- Each memory receives a **discounted reward** using a temporal decay (`γ`).
- Folding results in an immediate penalty.
- Winning/loss rewards are scaled relative to **money delta**.

### Memory and Replay Buffer Design
- Each agent has:
  - A **short-term buffer** (per hand)
  - A **cumulative buffer** (per generation)
- Experiences are sampled from both during training.
- Negative experiences (e.g., illegal actions) are stored and trained on as needed.

---

## Architecture Summary

| Component       | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `Table`         | Orchestrates the game loop, betting rounds, and shared state              |
| `Player`        | Encodes player money, hand, actions, and training state                   |
| `HoldEm`        | Poker engine: card dealing, pot handling, winner determination            |
| `HandRanker`    | Computes full hand rankings from community + hole cards                   |
| `DQN`           | Dueling Double DQN with custom training and action selection              |
| `ReplayBuffer`  | Experience memory with `sample()` and `merge_buffers()` methods           |

---

## Training Flow

1. **Initialize**: Random reward vectors + new Dueling DQNs for each player.
2. For each generation:
   - Train all agents for `N` episodes (hands).
   - Score agents based on:
     - Hands lost
     - Fold frequency
     - Busts
   - Generate new reward vectors:
     - Top 2 → mutate → overwrite bottom 4
     - Middle 2 → mutate → overwrite next 2
   - Store all updated models and reward vectors.

---

## Game Design Notes

- **State Encoding** includes:
  - One-hot card encodings (52 for hole, 52 for community)
  - Pot, current raise, player money, betting stage (one-hot)
  - For each other player: fold flag, raise amount, total bet

- **Action Space (10 actions)**:
  - 0–6: different raise sizes (relative % of stack)
  - 7: call
  - 8: check
  - 9: fold

- **Legal actions** are filtered, and illegal moves trigger a negative reward + re-sample.

---

## Future Improvements

- Add epsilon decay during training
- Add multi-table parallel generation evolution (cross-table gene mixing)
- Normalize model evaluation across more networks
- Build human-vs-model demo interface

---

## Notes

This system was built under **hardware constraints** on a 6-year-old laptop with 16 GB RAM. Despite that, it successfully demonstrates:
- A full RL-based Hold'em engine
- Reward vector evolution
- Independent Q-networks competing via shared environment

The framework can be scaled horizontally with more compute (parallel training, threading, larger buffers) or extended with more sophisticated learning heuristics.

---
