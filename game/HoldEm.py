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

        #debug self.logger.log("Num Cards: " + str(len(self.deck.cards)))
        #debug self.logger.log("Deck: " + str(self.deck))

    def update_pot(self):
        self.pot = 0
        for player_key in self.players:
            self.pot += self.players[player_key].total_bet
    def river(self):
        self.update_pot()
        c = self.deck.deal_card()
        #debug self.logger.log("River: " + str(c))
        c.visible = True
        self.community_cards[4] = c
        self.community_cards_index += 1

    def turn(self):
        self.update_pot()
        c = self.deck.deal_card()
        #debug self.logger.log("Turn: " + str(c))
        c.visible = True
        self.community_cards[3] = c
        self.community_cards_index += 1

    def flop(self):
        self.update_pot()
        #debug self.logger.log("Flop: ")
        for i in range(3):
            c = self.deck.deal_card()
            c.visible = True
            self.community_cards[i] = c
            #debug self.logger.log("\t" + str(c))
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
        #debug self.logger.log("Dealing Hands: ")
        for player_key, player in self.players.items():
            
            card1 = self.deck.deal_card()
            card2 = self.deck.deal_card()
            #debug self.logger.log("Player :" + player_key, end = "")
            #debug self.logger.log(f"({card1}, {card2})")
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

        #debug self.logger.log("Distributing Pot: ")
        #debug self.logger.log("Players Still Playing: ")

        active_players = [key for key, player in self.players if not player.folded]

        for player_key in self.players:
            self.last_winners[player_key] = 0
            if not self.players[player_key].folded:
                
                #debug self.logger.log(str(player_key))

                num_players_still_in +=1
                player_hand = self.players[player_key].get_hand()
                #catch case for a pre-flop win
                if player_hand:
                    player_hands[player_key] = player_hand.get_cards()
                else: 
                    player_hands[player_key] = None

        if num_players_still_in == 1:
            #debug self.logger.log("Only one player still in the game.")
            winner_key = active_players[0]
            self.players[winner_key].total_money += self.pot
            self.players[winner_key].total_bet = 0
            return

        #debug self.logger.log("Cards still in hole: " )
        #for card in self.community_cards:
            #debug self.logger.log("\t" + str(card))

        #if there is more than 1 winner, that means the hand was concluded
        hand_ranks = rank_players(self.community_cards, player_hands)

        leftovers = None
        next_min_offset = 0
        for ranked_player_list in hand_ranks:

            while(len(ranked_player_list) != 0):
                min_bet_key = min(self.players, key=lambda k: self.players[k].total_bet if self.players[k].total_bet > 0 else float('inf'))

                min_bet = self.players[min_bet_key].total_bet # smallest potential subpot
                #gets all players that bet on this subpot and haven't folded
                subpot_contributors = [player_key for player_key, player in self.players.items() if player.total_bet > 0] 
                subpot = 0
                #returns rewards 
                for subpot_contributor in subpot_contributors:
                    player = self.players[subpot_contributor]
                    player_bet = player.total_bet
                    if player_bet <= min_bet:
                        subpot += player_bet
                        player.total_bet = 0
                    else:
                        player.total_bet -= min_bet
                        subpot += min_bet

                eligible_winners = [key for key in ranked_player_list if key in subpot_contributors and not self.players[key].folded]

                ineligible_in_subpot = [key for key in ranked_player_list if key in subpot_contributors]
                #catch case if there are no eligible winners in the list
                if not eligible_winners:
                    next_min_offset += 1
                    leftovers += ineligible_in_subpot
                    break
                next_min_offset = 0

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
            player.total_money += player.total_bet
            player.total_bet = 0 


    def get_bets_that_match(self, sorted_bets, current_max_bet):
        bets_that_match = []
        for bet, player_obj in sorted_bets:
            if not bet == current_max_bet:
                break
            bets_that_match.append((bet, player_obj))
        return bets_that_match
            
    def distribute_potv2(self):
        self.logger.log("Distributing pot: ")
        player_hands = {}
        num_players_still_in = 0

        #debug self.logger.log("Distributing Pot: ")
        #debug self.logger.log("Players Still Playing:")

        active_players = [key for key, player in self.players.items() if not player.folded]

        for player_key in self.players:
            self.last_winners[player_key] = 0
            if not self.players[player_key].folded:
                #debug self.logger.log(str(player_key))
                num_players_still_in += 1
                player_hand = self.players[player_key].get_hand()
                if player_hand:
                    player_hands[player_key] = player_hand.get_cards()
                else:
                    player_hands[player_key] = None

        if num_players_still_in == 1:
            #debug self.logger.log("Only one player still in the game.")
            winner_key = active_players[0]
            self.players[winner_key].total_money += self.pot
            self.players[winner_key].total_bet = 0
            self.pot = 0
            return

        #debug self.logger.log("Cards still in hole:")
        #for card in self.community_cards:
            #debug self.logger.log("\t" + str(card))

        hand_ranks = rank_players(self.community_cards, player_hands)

        next_min_offset = 0

        # sort players by total_bet descending
        sorted_players = sorted(
            self.players.keys(),
            key=lambda player_key: (self.players[player_key].total_bet, player_key),
            reverse=True
        )

        # prevent only one player from trying to win against himself
        assert len(sorted_players) >= 2, "Need 2 or more players to play a hand."

        # get the keys
        highest_bet_key = sorted_players[0]
        second_highest_bet_key = sorted_players[1]

        # get their bets
        highest_bet = self.players[highest_bet_key].total_bet
        second_highest_bet = self.players[second_highest_bet_key].total_bet

        # if they dont match, clip the highest bet to the called bet level
        bet_difference = highest_bet - second_highest_bet
        if bet_difference > 0:
        
            
            highest_player = self.players[highest_bet_key]

            highest_player.total_money += bet_difference
            highest_player.total_bet -= bet_difference

        for i in range(len(hand_ranks)):
            ranked_player_list = hand_ranks[i]
            while len(ranked_player_list) != 0:
                subpot_contributors = [key for key, p in self.players.items() if p.total_bet > 0]
                self.logger.log("Subpot Contributors: " + str(subpot_contributors))
                if not subpot_contributors:
                    break

                sorted_contributors = sorted(subpot_contributors, key=lambda k: self.players[k].total_bet)
                if next_min_offset >= len(sorted_contributors):
                    break  # safety check

                min_bet_key = sorted_contributors[next_min_offset]
                min_bet = self.players[min_bet_key].total_bet
                self.logger.log("Min Bet: " + str(min_bet))
                refund = {}
                subpot = 0
                for key in subpot_contributors:
                    player = self.players[key]
                    #grabs the total bet prior to modifying the bet
                    refund[key] = player.total_bet
                    if player.total_bet <= min_bet:
                        subpot += player.total_bet
                        player.total_bet = 0
                    else:
                        subpot += min_bet
                        player.total_bet -= min_bet
                self.logger.log("Total Subpot: " + str(subpot))
                eligible_winners = [key for key in ranked_player_list if key in subpot_contributors and not self.players[key].folded]
                if len(eligible_winners) == 0:
                    for key in refund:
                        self.players[key].total_bet += refund[key]
                    next_min_offset += 1
                    break
                else:
                    next_min_offset = 0
                self.logger.log("Subpot has eligible winners")
                amount_per_winner = subpot / len(eligible_winners)
                for player_key in eligible_winners:
                    self.last_winners[player_key] += amount_per_winner
                    self.players[player_key].total_money += amount_per_winner
                    self.pot -= amount_per_winner

                for i in range(len(ranked_player_list) - 1, -1, -1):
                    
                    if self.players[ranked_player_list[i]].total_bet == 0:
                        self.logger.log("Dropping player: " + str(ranked_player_list[i]))
                        del ranked_player_list[i]

            if self.pot == 0:
                break
        self.logger.log("Leftover Cleanup: ")
        # Clear any remaining bets (typically 0 at this point)
        for player in self.players.values():
            self.logger.log(f"Total Money: {str(player.total_money)}, Total Bet: {str(player.total_bet)}")
            player.total_money += player.total_bet
            player.total_bet = 0

    def reset(self):
        self.distribute_potv2()
        #return each card from hands

        #debug self.logger.log("Deck: " + str(self.deck))

        #debug self.logger.log("Returning Cards: ")
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
        #debug self.logger.log("Num Cards: " + str(len(self.deck.cards)))
        #debug self.logger.log("Deck: " + str(self.deck))


        self.deck.shuffle()