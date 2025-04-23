class Memory():
    def __init__(self, prev_state, action, reward, post_state, is_done=False):
        self.state = prev_state
        self.action = action
        self.reward = reward
        self.next_state = post_state
        self.is_done = is_done

    def merge_value_with_str(self, input_str, value):
        input_str += value + ", "
        return input_str

def __str__(self):
    return (
        f"Starting State:\n{', '.join(str(v) for v in self.state)}\n"
        f"Action: {self.action}\n"
        f"Reward: {self.reward}\n"
        f"Finished: {self.is_done}\n"
        f"Next State:\n{', '.join(str(v) for v in self.next_state)}"
    )

