class Memory():
    def __init__(self, prev_state, action, reward, post_state, is_done=False):
        self.state = prev_state
        self.action = action
        self.reward = reward
        self.next_state = post_state
        self.is_done = is_done
