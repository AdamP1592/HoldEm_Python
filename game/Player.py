class Player:
    def __init__(self):
        self.hand = None
        self.folded = False
        self.checked = False
        self.raised = False
        self.raise_amount = 0
        self.total_bet = 0
        self.total_money = 5000

        self.raise_applied = True

    

    def set_hand(self, h):
        self.hand = h

    def get_hand(self):
        return self.hand

    def check(self):
        if not self.folded:
            self.raised = False
            self.checked = True
            self.raise_amount = 0
            return True
        return False

    def raise_(self, raise_amount):    
        if not self.folded and (raise_amount <= (self.total_money - self.total_bet)):
            self.raise_applied = False
            self.raised = True
            self.checked = False

            self.total_money -= raise_amount
            self.raise_amount = raise_amount
            self.total_bet += raise_amount
            return True
        return False

    def fold(self):
        self.folded = True

    def call(self, amount):
        #amount is the total amount a player has bet in order to match
        amount_needed_to_match = amount - self.raise_amount

        if not self.folded:
            #flags get set when a call is applied
            self.checked = True
            self.raised = False
            # since the call is effectively a raise to the current bet amount
            self.raise_applied = False 

            if (amount_needed_to_match <= self.total_money):
                self.total_money -= amount_needed_to_match
                self.raise_amount = amount_needed_to_match
                self.total_bet += amount_needed_to_match
            else:
                self.total_bet += self.total_money
                self.raise_amount = self.total_money
                self.total_money = 0

                
            return True
        
        return False

    def next_turn(self):
        self.raise_amount = 0
        self.checked = False
        self.raised = False

    def reset(self):
        cards_in_hand = [card for card in self.hand.get_hand()] # shallow copy, but not just reference to list
        self.next_turn()
        self.folded = False
        self.total_bet = 0
        self.hand = None
        return cards_in_hand
