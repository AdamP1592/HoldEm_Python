from dqn import *
def test_reset():
    ## MAKE SURE YOU REMOVE THE RELATIVE IMPORT FROM DQN FOR MEMRORY AND REPLACE IT WITH THE 
    ## ABSOLUTE IMPORT (Change .Memory to Memory)
    network = simple_dqn(10, 12)
    network.reset()

if __name__ == "__main__":
    test_reset()