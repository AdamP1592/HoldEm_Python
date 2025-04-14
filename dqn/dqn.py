import tensorflow as tf
class dqn():
    def __init__(self, network_structure):
        output_layer = tf.keras.layers.Dense(network_structure[len(network_structure) - 1])
        del network_structure[-1]
        layers = [tf.keras.layers.Dense(num_neurons, activation=tf.nn.leaky_relu) for num_neurons in network_structure]
        layers.append(output_layer)

        self.model = tf.keras.Sequential(layers)
        self.target_model = tf.keras.Sequential(layers)


        self.optimizer = tf.keras.optimizers.Adam
        self.loss_fn = tf.keras.losses.Huber

        self.metrics = ['mae']
        self.gamma = 0.99
        self.num_acitons = network_structure[0] - 1

    def calc_qs(self, outputs):
        advantages = outputs[:, :-1]
        value = outputs[:, -1:]
        advantage_mean = tf.reduce_mean(advantages, axis=1, keepdims=True)

        q_values = value + (advantages - advantage_mean)
        
        return q_values

    def get_model_output(self, state):
        outputs = self.model(state)
        return self.calc_qs(outputs)
        
    @tf.function
    def batch_train(self, states, actions, rewards, next_states, dones):
        with tf.GradientTape() as tape:

            #main state
            outputs = self.model(states)
            q_values = self.calc_qs(outputs)
            action_mask = tf.one_hot(actions, self.num_actions)
            q_sa = tf.reduce_sum(q_values * action_mask, axis=1)
            tf.print("Q(s, a): ", q_sa)
            #
            next_outputs = self.model(next_states)
            next_q_values = self.calc_qs(next_outputs)

            next_actions = tf.argmax(next_q_values, axis=1)
            tf.print("Action: ", next_actions)

            next_target_output = self.target_model(next_states)
            next_target_qs = self.calc_qs(next_target_output)

            next_action_mask = tf.one_hot(next_actions, self.num_actions)

            q_next = tf.reduce_sum(next_target_qs * next_action_mask, axis = 1)
            tf.print("Q(s', a'): ", q_next)

            targets = rewards + self.gamma *  (1.0 - dones) * q_next
            tf.print("targets: ", targets)
            loss = self.loss_fn(targets, q_sa)
            tf.print("Loss ", loss)

        gradients = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))
        return tf.reduce_mean(loss)

    def copy_main_to_target(self):
        self.target_model = tf.keras.models.clone_model(self.model)
        self.target_model.set_weights(self.model.get_weights())

class simple_dqn(dqn):
    def __init__(self, num_input, num_outputs):
        structure = [num_input, 64, 64, 32, 32, 16, 16, num_outputs, num_outputs, num_outputs]
        super.__init__(structure)
