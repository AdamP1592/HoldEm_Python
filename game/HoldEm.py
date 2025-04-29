import random
from game.Deck import Deck
from game.Hand import Hand
from game.Player import Player
from game.HandRanker import rank_players
from game.Logger import Logger

class HoldEm:
    def __init__(self, num_decks):
        self.vs_code_command = "chcp 65001"
        self.hands = []
        self.players = {}
        self.deck = Deck(num_decks)
        self.min_bet = 50
        self.pot = 0
        self.community_cards = [None] * 5
        self.community_cards_index = 0

        self.logger = Logger(reset=False)

        self.last_winners = {}

        self.logger.log("Num Cards: " + str(len(self.deck.cards)))
        self.logger.log("Deck: " + str(self.deck))

    def update_pot(self):
        self.pot = 0
        for player_key in self.players:
            self.pot += self.players[player_key].total_bet
    def river(self):
        self.update_pot()
        c = self.deck.deal_card()
        self.logger.log("River: " + str(c))
        c.visible = True
        self.community_cards[4] = c
        self.community_cards_index += 1

    def turn(self):
        self.update_pot()
        c = self.deck.deal_card()
        self.logger.log("Turn: " + str(c))
        c.visible = True
        self.community_cards[3] = c
        self.community_cards_index += 1

    def flop(self):
        self.update_pot()
        self.logger.log("Flop: ")
        for i in range(3):
            c = self.deck.deal_card()
            c.visible = True
            self.community_cards[i] = c
            self.logger.log("\t" + str(c))
        self.community_cards_index = 2


    def rank_hands(self):
        from game import HandRanker
        handValues = {}

        for playerKey in self.players.keys():
            if not self.players[playerKey].folded:
                player_hand = self.players[playerKey].get_hand()
                handValues[playerKey] = HandRanker.get_best_hand_value(player_hand, self.community_cards)
        
        return handValues

    def get_community_cards(self):
        comm_cards = self.community_cards[:self.community_cards_index + 1]
        return comm_cards

    def remove_player(self, player_id):
        if player_id in self.players:
            del self.players[player_id]

    def add_player(self, player_id, player):
        self.players[player_id] = player

    def deal_hands(self):
        self.pot = 0
        self.logger.log("Dealing Hands: ")
        for player_key, player in self.players.items():
            
            card1 = self.deck.deal_card()
            card2 = self.deck.deal_card()
            self.logger.log("Player :" + player_key, end = "")
            self.logger.log(f"({card1}, {card2})")
            player.hand = Hand([card1, card2])
            

    def print_deck(self):
        cards = self.deck.get_all_cards()
        for card in cards:
            print(card.get_name(), end=" ")
        print()

    def print_hands(self):
        for player in self.players.values():
            
            print(str(player.hand.to_true_string()))

    def get_player_bet(self, player_key):
        return self.players[player_key].total_bet
    
    def distribute_pot(self):
        player_hands = {}
        num_players_still_in = 0

        self.logger.log("Distributing Pot: ")
        self.logger.log("Players Still Playing: ")

        for player_key in self.players:
            self.last_winners[player_key] = 0
            if not self.players[player_key].folded:
                
                self.logger.log(str(player_key))

                num_players_still_in +=1
                player_hand = self.players[player_key].get_hand()
                #catch case for a pre-flop win
                if player_hand:
                    player_hands[player_key] = player_hand.get_cards()
                else: 
                    player_hands[player_key] = None

        if num_players_still_in == 1:
            self.logger.log("Only one player still in the game.")

            keys = list(self.players.keys())
            player_key = keys[0]
            self.players[player_key].total_money += self.pot
            self.players[player_key].total_bet = 0
            return

        self.logger.log("Cards still in hole: " )
        for card in self.community_cards:
            self.logger.log("\t" + str(card))

        #if there is more than 1 winner, that means the hand was concluded
        hand_ranks = rank_players(self.community_cards, player_hands)
        for ranked_player_list in hand_ranks:

            while(len(ranked_player_list) != 0):
                min_bet_key = min(self.players, key=lambda k: self.players[k].total_bet if self.players[k].total_bet > 0 else float('inf'))

                min_bet = self.players[min_bet_key].total_bet # smallest potential subpot

                subpot_contributors = [player_key for player_key, player in self.players.items() if player.total_bet > 0] 
                subpot = 0
                for subpot_contributor in subpot_contributors:
                    player = self.players[subpot_contributor]
                    player_bet = player.total_bet
                    if player_bet <= min_bet:
                        subpot+= player_bet
                        player.total_bet = 0
                    else:
                        player.total_bet -= min_bet
                        subpot += min_bet

                eligible_winners = [key for key in ranked_player_list if key in subpot_contributors]
                #catch case if there are no eligible winners in the list
                if not eligible_winners:
                    break

                amount_per_winner = subpot/len(eligible_winners)
                #applies the money to the winners
                for player_key in eligible_winners:
                    self.last_winners[player_key] += amount_per_winner
                    self.players[player_key].total_money += amount_per_winner
                    self.pot -= amount_per_winner
                #remove any winner that had their bet zeroed out
                for player_key_ind in range(len(ranked_player_list) - 1, -1, -1):
                    player_key = ranked_player_list[player_key_ind]
                    if self.players[player_key].total_bet == 0:
                        del ranked_player_list[player_key_ind]
            if self.pot == 0:
                break
        for player in self.players.values():
            player.total_bet = 0
  
    def reset(self):
        self.distribute_pot()
        #return each card from hands

        self.logger.log("Deck: " + str(self.deck))

        self.logger.log("Returning Cards: ")
        for key in self.players.keys():
            cards = self.players[key].reset()
            if cards:
                for card in cards:
                    self.deck.return_card(card)
        
        #return each card from community cards 
        for cardInd in range(len(self.community_cards)):
            #since a hand can end before all cc are in the hole
            if self.community_cards[cardInd] != None:
                self.deck.return_card(self.community_cards[cardInd])
                self.community_cards[cardInd] = None

        self.community_cards_index = 0
        self.logger.log("Num Cards: " + str(len(self.deck.cards)))
        self.logger.log("Deck: " + str(self.deck))


        self.deck.shuffle()