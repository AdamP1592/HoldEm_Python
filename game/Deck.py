import random
from game.Card import Card

class Deck:
    def __init__(self, num_decks):
        self.suit_chars = ['\u2660', '\u2665', '\u2666', '\u2663']
        self.suits = ["spade", "heart", "diamond", "club"]
        self.cards = []
        self.num_decks = num_decks
        self.size = num_decks * 52
        self.setup_decks()
        self.shuffle()

    def setup_decks(self):
        self.cards.clear()
        face_cards = [10, 11, 12]
        face_card_names = ["J", "Q", "K"]
        for _ in range(self.num_decks):
            for suit_index in range(len(self.suits)):
                for j in range(13):
                    card_id = suit_index * 13 + j  # unique card index from 0 to 51
                    normalized_id = card_id / 51.0 

                    idx = self.index_of(face_cards, j)
                    if j == 0:
                        card = Card(1, "A" + self.suit_chars[suit_index], self.suits[suit_index], high_value=14)
                    elif idx != -1:
                        card = Card(j + 1, face_card_names[idx] + self.suit_chars[suit_index], self.suits[suit_index])
                    else:
                        card = Card(j + 1, str(j + 1) + self.suit_chars[suit_index], self.suits[suit_index])

                    card.id = normalized_id
                    self.cards.append(card)

    def size_(self):
        return self.size

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if not self.cards:
            raise Exception("No cards left in the deck.")
        card = self.cards.pop()
        self.size -= 1
        return card

    def return_card(self, card):
        self.cards.append(card)
        self.size+=1

    def index_of(self, ls, val):
        for i, item in enumerate(ls):
            if item == val:
                return i
        return -1

    def get_all_cards(self):
        return tuple(self.cards)
