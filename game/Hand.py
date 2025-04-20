class Hand:
    def __init__(self, cards):
        self.hand = list(cards)

    def get_visible_value(self):
        value_sum = sum(card.get_value() for card in self.hand)
        if value_sum > 21:
            value_sum = -1
        return value_sum

    def get_true_value(self):
        if not self.hand:
            return 0
        original = self.hand[0].visible
        self.hand[0].visible = True
        value_sum = sum(card.get_value() for card in self.hand)
        self.hand[0].visible = original
        if value_sum > 21:
            value_sum = -1
        return value_sum

    def get_cards(self):
        return self.hand

    def __str__(self):
        return " ".join(card.get_name() for card in self.hand)

    def to_true_string(self):
        if not self.hand:
            return ""
        self.hand[0].visible = True
        self.hand[1].visible = True
        s = " ".join(card.get_name() for card in self.hand)
        return s

    def add_card(self, card):
        self.hand.append(card)
