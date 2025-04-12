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
            self.checked = True
            return True
        return False

    def raise_(self, raise_amount):
        self.checked = False
        if not self.folded and (raise_amount <= (self.total_money - self.total_bet)):
            self.raised = True
            self.raise_amount = raise_amount
            self.total_bet += raise_amount
            return True
        return False

    def fold(self):
        self.folded = True

    def call(self, amount):
        if not self.folded and (amount <= (self.total_money - self.total_bet)):
            self.checked = True
            self.total_bet += amount
            return True
        return False

    def next_turn(self):
        self.raise_amount = 0
        self.checked = False
        self.raised = False

    def reset(self):
        self.next_turn()
        self.folded = False
        self.total_bet = 0
        self.hand = None
        return self.hand
