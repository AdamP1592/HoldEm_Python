import tensorflow as tf
import numpy as np

from .Memory import Memory

import random
class DQN():
    def __init__(self, network_structure, num_episodes = -1):
        self.network_structure = network_structure[:]

        self.metrics = ['mae']
        self.gamma = 0.99
        self.num_actions = network_structure[-1] - 1

        self.num_episodes = num_episodes

        self.num_memories_trained = 0
        self.episode_count = 0
        
        self.build_model(network_structure)

    def get_layers(self, network_structure):
        network_structure = network_structure[:]
        output_layer = tf.keras.layers.Dense(network_structure[len(network_structure) - 1])
        del network_structure[-1]

        layers = [tf.keras.layers.Dense(num_neurons, activation=tf.nn.leaky_relu) for num_neurons in network_structure]
        layers.append(output_layer)

        return layers

    def build_model(self, network_structure):

        layers = self.get_layers(network_structure)
        self.model = tf.keras.Sequential(layers)
        self.model.build(input_shape=(None, network_structure[0]))

        layers = self.get_layers(network_structure)
        self.target_model = tf.keras.Sequential(layers)
        self.target_model.build(input_shape=(None, network_structure[0]))
        
        #WRAPPED FUNCTION
        self.batch_train = tf.function(self.unwrapped_batch_train)

        self.copy_main_to_target()
        self.optimizer = tf.keras.optimizers.Adam()
        self.loss_fn = tf.keras.losses.Huber()

        if self.num_episodes != -1:
            #add decay
            pass
    

    def reset(self):
        self.build_model(self.network_structure)
        self.num_memories_trained = 0
        self.episode_count = 0

    def calc_qs(self, outputs):
        advantages = outputs[:, :-1]
        value = outputs[:, -1:]
        advantage_mean = tf.reduce_mean(advantages, axis=1, keepdims=True)

        q_values = value + (advantages - advantage_mean)
        
        return q_values

    def get_model_output(self, state):
        outputs = self.model(state)
        return self.calc_qs(outputs)
    
    def unwrapped_batch_train(self, states:tf.Tensor, actions:tf.Tensor, rewards:tf.Tensor, next_states:tf.Tensor, dones:tf.Tensor) -> float:
        with tf.GradientTape() as tape:
            #main state
            outputs = self.model(states)
            q_values = self.calc_qs(outputs)
            action_mask = tf.one_hot(actions, self.num_actions)
            q_sa = tf.reduce_sum(q_values * action_mask, axis=1)
            
            #debug  tf.print("Q(s, a): ", q_sa)
            
            next_outputs = self.model(next_states)
            next_q_values = self.calc_qs(next_outputs)

            next_actions = tf.argmax(next_q_values, axis=1)
            #debug tf.print("Action: ", next_actions)

            next_target_output = self.target_model(next_states)
            next_target_qs = self.calc_qs(next_target_output)

            next_action_mask = tf.one_hot(next_actions, self.num_actions)

            q_next = tf.reduce_sum(next_target_qs * next_action_mask, axis = 1)
            #debug tf.print("Q(s', a'): ", q_next)

            targets = rewards + self.gamma *  (1.0 - dones) * q_next
            #debug tf.print("targets: ", targets)
            loss = self.loss_fn(targets, q_sa)
            #debug tf.print("Loss ", loss)

        gradients = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))

        return float(tf.reduce_mean(loss))

    def batch_train_memories(self, memory_sample: list[Memory]) -> float:


        ## here 
        states = np.array([mem.state for mem in memory_sample], dtype=np.float32)
        actions = np.array([mem.action for mem in memory_sample], dtype=np.int32)
        next_states = np.array([mem.next_state for mem in memory_sample], dtype=np.float32)
        rewards = np.array([mem.reward for mem in memory_sample], dtype=np.float32)
        dones = np.array([float(mem.is_done) for mem in memory_sample], dtype=np.float32)
        
        self.num_memories_trained += len(memory_sample)
        self.episode_count += 1

    # Now convert to tensors (only once)
        loss =  self.batch_train(
            tf.constant(states),
            tf.constant(actions),
            tf.constant(rewards),
            tf.constant(next_states),
            tf.constant(dones)
        )
        ## here
        if self.num_memories_trained > 500:
            self.num_memories_trained = 0
            self.copy_main_to_target()

        return loss

    def forward(self, state, epsilon = 0.1) -> int:
        if random.random() < epsilon:
            return random.randint(0, self.num_actions -1)
        
        if not isinstance(state, np.ndarray):
            state = np.array(state, dtype=np.float32)
        state = tf.expand_dims(state, axis=0)
        outputs = self.model(state)
        actions = self.calc_qs(outputs)

        return int(tf.argmax(actions, axis=1)[0].numpy())
    
    def copy_main_to_target(self):
        self.target_model.set_weights(self.model.get_weights())

class simple_dqn(DQN):
    def __init__(self, num_inputs, num_outputs, num_episodes = -1):
        structure = [num_inputs, int(num_inputs * 1.25), int(num_inputs * 1.0), int(num_inputs *0.75), int(num_inputs * 0.75), int(num_inputs * 0.5), int(num_inputs * 0.5), int(num_inputs * 0.5), int(num_inputs * 0.25), int(num_inputs * 0.5), num_outputs + 1, num_outputs + 1]
        super().__init__(structure, num_episodes)
