import random
class ReplayBuffer():

    
    def __init__(self, max_entries):
        self.buffer = []
        self.max_entries = max_entries
    
    def store_memory(self, memory):
        if len(self.buffer) > self.max_entries:
            del self.buffer[0]

        self.buffer.append(memory)
    
    def sample(self, num_entries):
        sample = []
        for i in range(num_entries):
            sample.append(random.randint(0, len(self.buffer) - 1))

    def __len__(self):
        return len(self.buffer)