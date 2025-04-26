class Card:
    def __init__(self, card_value, card_name, suit, high_value=-1):
        self.visible = True
        self.card_name = card_name
        self.card_value = card_value
        self.high_value = high_value
        self.suit = suit
        self.id = None
        self.set_encoded_value()


    def set_encoded_value(self):
        suits = ["spade", "heart", "diamond", "club"]
        suit_ind = suits.index(self.suit)
        encoded_suit = suit_ind * 13
        encoded_card = encoded_suit + self.card_value
        self.normalized_encoded_val = encoded_card

    def get_encoded_value(self):
        return self.normalized_encoded_val


    def get_value(self, is_high=False):
        if self.visible:
            if is_high and self.high_value != -1:
                return self.high_value
            return self.card_value
        else:
            return 0

    def get_name(self):
        if self.visible:
            return self.card_name
        else:
            return "**"
        
    def get_true_name(self):
        return self.card_name

    def __str__(self):
        return f"{self.get_true_name()} of {self.suit}"
