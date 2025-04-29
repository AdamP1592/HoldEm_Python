import random

from game.Logger import Logger
class ReplayBuffer():

    def __init__(self, max_entries):
        self.buffer = []
        self.max_entries = max_entries
        self.logger = Logger()
    
    def store_memory(self, memory):
        if len(self.buffer) > self.max_entries:
            self.buffer[0]
        self.buffer.append(memory)
    
    def sample(self, num_entries:int)->list:
        sample = []
        num_entries = min(num_entries, len(self.buffer))
        for i in range(num_entries):
            memory = self.buffer[random.randint(0, len(self.buffer) - 1)]
            sample.append(memory)
        return sample

    def __len__(self):
        return len(self.buffer)

    def merge_buffers(self, input_buffer):
        for memory in input_buffer.buffer:
            self.store_memory(memory)

    def merge_percentage_of_self(self, input_buffer, percentage = 0.05):
        amount_from_input = int(percentage * len(self.buffer))
        print("Num memories: ", len(self.buffer))
        if amount_from_input > len(input_buffer):
            print("Percentage was greater than buffer")
            amount_from_input = len(input_buffer)

        input_memories = input_buffer.sample(amount_from_input)
        self.logger.log("Merging Buffers")

        for mem in input_memories:
            self.logger.log(str(mem))
            print(mem)
            self.store_memory(mem)

            