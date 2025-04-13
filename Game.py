from game.Table import Table

from game.Deck import Deck
table = Table()
players = []

def buildTable(numPlayers:int):
    global table
    global players
    for i in range(numPlayers):
        players += table.add_player()
    
    

if __name__ == "__main__":
    buildTable(5)
    d = Deck(1)
    cards = d.cards
    for card in cards:
        card.visible = True
        print(card.get_true_name(), " ", card.get_value(True))

    for i in range(1):
        table.game.deal_hands()

        table.advance_stage()
        table.game.get_community_cards()
        table.advance_stage()
        table.game.get_community_cards()
        table.advance_stage()
        cards = table.game.get_community_cards()

        table.game.print_hands()

        for card in cards:
            print(card.get_true_name(), end = " ")
        print()
        

        table.advance_stage()
    
    
    #table.game.rank_hands()
    