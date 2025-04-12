from game.HoldEm import HoldEm
from game.Table import Table
table = Table()
players = []

def buildTable(numPlayers:int):
    global table
    global players
    for i in range(numPlayers):
        players += table.add_player()
    
    

if __name__ == "__main__":
    buildTable()

    table
    