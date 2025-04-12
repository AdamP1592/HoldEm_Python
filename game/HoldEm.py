import random
from game.Deck import Deck
from game.Hand import Hand
from game.Player import Player

class HoldEm:
    def __init__(self, num_decks):
        self.vs_code_command = "chcp 65001"
        self.hands = []
        self.players = {}
        self.deck = Deck(num_decks)
        self.min_bet = 50
        self.pot = []
        self.community_cards = [None] * 5
        self.community_cards_index = 0

        self.hands = ["Royal Straight Flush",
                      "Straight Flush",
                      "4 of a kind",
                      "Full House",
                      "Flush",
                      "Straight",
                      "Three of a kind",
                      "Two Pair",
                      "Pair",
                      "High Card"]

    def river(self):
        c = self.deck.deal_card()
        c.visible = True
        self.community_cards[4] = c
        self.community_cards_index += 1

    def turn(self):
        c = self.deck.deal_card()
        c.visible = True
        self.community_cards[3] = c
        self.community_cards_index += 1

 
            


    def rank_hands(self, hand:Hand):
        """
            Ranks: royal straight flush
            straight flush(with highest total card value)
            4 of a kind
            full house
            flush
            straight
            3 of a kind
            2 pair
            pair
            high card
        
        """
        cards = hand.get_hand()

    def finish_round(self):
        hands = {}
        for player_key in self.players.keys():
            if not self.players[player_key].folded:
                hands[player_key] = self.players.get_hand()

    def flop(self):
        for i in range(3):
            c = self.deck.deal_card()
            c.visible = True
            self.community_cards[i] = c
        self.community_cards_index = 3 - 1

    def get_community_cards(self):
        comm_cards = self.community_cards[:self.community_cards_index + 1]
        for card in comm_cards:
            if(card != None):
                print(card.get_name(), end=" ")
        print()
        return comm_cards

    def remove_player(self, player_id):
        if player_id in self.players:
            del self.players[player_id]

    def add_player(self, player_id, player):
        self.players[player_id] = player

    def deal_hands(self):
        num_players = len(self.players)
        self.pot = [0] * num_players
        for player in self.players.values():
            card1 = self.deck.deal_card()
            card1.visible = False
            card2 = self.deck.deal_card()
            card2.visible = False
            player.hand = Hand([card1, card2])
            self.hands.append(player.hand)

    def print_deck(self):
        cards = self.deck.get_all_cards()
        for card in cards:
            print(card.get_name(), end=" ")
        print()

    def print_hands(self):
        for player in self.players.values():
            print(str(player.hand))
    
    def reset(self):
        #return each players hand to the deck
        for key in self.players.keys():
            cards = self.players[key].reset()
            for card in cards:
                self.deck.return_card(card)
        
        #return each card from community cards
        for cardInd in range(len(self.community_cards)):
            self.deck.return_card(self.community_cards[cardInd])
        self.community_cards.clear()

        self.deck.shuffle()