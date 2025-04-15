class Player:
    def __init__(self):
        self.hand = None
        self.folded = False
        self.checked = False
        self.raised = False
        self.raise_amount = 0
        self.total_bet = 0
        self.total_money = 5000

    

    def set_hand(self, h):
        self.hand = h

    def get_hand(self):
        return self.hand

    def check(self):
        if not self.folded:
            self.raised = False
            self.checked = True
            return True
        return False

    def raise_(self, raise_amount):
        
        if not self.folded and (raise_amount <= (self.total_money - self.total_bet)):
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
        if not self.folded and (amount <= (self.total_money - self.total_bet)):
            self.checked = True
            self.raised = False
            self.total_bet += amount
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
