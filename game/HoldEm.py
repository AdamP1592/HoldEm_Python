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

    def rank_hands(self):
        from game import HandRanker
        handValues = {}

        for playerKey in self.players.keys():
            if not self.players[playerKey].folded:
                player_hand = self.players[playerKey].get_hand()
                handValues[playerKey] = HandRanker.get_best_hand_value(player_hand, self.community_cards)
        
        return handValues

    def flop(self):
        for i in range(3):
            c = self.deck.deal_card()
            c.visible = True
            self.community_cards[i] = c
        self.community_cards_index = 3 - 1

    def get_community_cards(self):
        comm_cards = self.community_cards[:self.community_cards_index + 1]
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
            
            print(str(player.hand.to_true_string()))
    
    def reset(self):
        #return each players hand to the deck
        possible_ranks = ["Royal Straight Flush",
                      "Straight Flush",
                      "4 of a kind",
                      "Full House",
                      "Flush",
                      "Straight",
                      "Three of a kind",
                      "Two Pair",
                      "Pair",
                      "High Card"]
        
        player_ranks = []

        hand_ranks = self.rank_hands()

        for key in self.players.keys():
            hand_category = hand_ranks[key][0]
            hand_category_value = hand_ranks[key][1]
            hand_category_rank = possible_ranks.index(hand_category)
            player_ranks.append((key, hand_category_rank, hand_category_value))

        sorted_ranks = sorted(player_ranks, key=lambda x: x[1])

        for rank in sorted_ranks:
            print(self.players[rank[0]].get_hand().to_true_string())
            print(rank)
            print(possible_ranks[rank[1]])

        top_rank = sorted_ranks[0][1] # gets best hand rank
        top_ranks = []
        
        for hand_rank in sorted_ranks:# adds all hand ranks that match
            if top_rank != hand_rank[1]:
                break
            top_ranks.append(hand_rank)

        
        
        """for rank in top_ranks:
            print(self.players[rank[0]].get_hand().to_true_string())
        """
            

  
        #return each card from hands
        for key in self.players.keys():
            cards = self.players[key].reset()
            for card in cards:
                self.deck.return_card(card)
        
        #return each card from community cards
        for cardInd in range(len(self.community_cards)):
            self.deck.return_card(self.community_cards[cardInd])
        self.community_cards= [None] * 5
        self.community_cards_index = 0

        self.deck.shuffle()