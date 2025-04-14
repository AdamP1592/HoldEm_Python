from game.Table import Table

from game.Deck import Deck
table = Table()
players = []

def buildTable(numPlayers:int):
    global table
    global players
    for i in range(numPlayers):
        players.append(table.add_player())

if __name__ == "__main__":
    buildTable(5)
    raise_amount = 5
    for player in players:
        player.raise_(raise_amount)
        raise_amount += 1
    for i in range(1):
        table.game.deal_hands()

        base_hand = players[0].get_hand()
        for player in players:
            player.set_hand(base_hand)

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

                
        for player in players:
            print(player.total_money)
    
    
    #table.game.rank_hands()
    