from game.Logger import Logger
class Player:
    def __init__(self):
        self.hand = None
        #action flags
        self.folded = False
        self.checked = False
        self.raised = False
        #state flags
        self.all_in = False
        self.bust = False

        self.raise_amount = 0
        self.total_bet = 0
        self.total_money = 5000

        self.raise_applied = True

        self.logger = Logger()
        
        #SOLELY FOR DISPLAY PURPOSES
        self.called = False
    

    def set_hand(self, h):
        self.hand = h

    def get_hand(self):
        return self.hand

    def check(self):
        if not self.folded:
            self.called = False
    
            self.raised = False
            self.checked = True
            self.raise_amount = 0
            return True
        return False

    def raise_(self, raise_amount):  
        if self.folded:
            return False
        
        if raise_amount > self.total_money:
            raise_amount = self.total_money
        
        self.called = False

        self.raise_applied = False
        self.raised = True
        self.checked = False

        self.total_money -= raise_amount
        self.raise_amount += raise_amount
        self.total_bet += raise_amount
    
        return True

    def fold(self):
        self.folded = True
        self.raised = False
        self.checked = False

    def call(self, amount):
        #amount is the total amount a player has bet in order to match
        amount_needed_to_match = amount - self.raise_amount

        if not self.folded:
            #flags get set when a call is applied
            self.checked = True
            self.raised = False
            self.called = True
            # since the call is effectively a raise to the current bet amount
            self.raise_applied = False 

            if (amount_needed_to_match <= self.total_money):
                self.total_money -= amount_needed_to_match
                self.raise_amount += amount_needed_to_match
                self.total_bet += amount_needed_to_match
            else:
                self.total_bet += self.total_money
                self.raise_amount += self.total_money
                self.total_money = 0
                self.all_in = True
                
            return True
        
        return False

    def next_turn(self):
        self.raise_amount = 0
        self.checked = False
        self.raised = False
        self.called = False

    def reset(self):
        self.logger.log("Resetting Player")
        cards_in_hand = None
        if self.hand:
            cards_in_hand = [card for card in self.hand.get_cards()] # shallow copy, but not just reference to list
        self.next_turn()
        self.folded = False
        self.all_in = False
        self.total_bet = 0
        self.hand = None
        return cards_in_hand
    def print_hand(self):
        print()
        if self.hand:
            print("Cards: ", end =" ")
            for card in self.hand.get_cards():
                print(card, end = "")
            print()
    def get_hand_str(self):
        if self.hand:
            return self.hand.to_true_string()