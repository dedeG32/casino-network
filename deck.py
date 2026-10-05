import random
import time
from unittest import case

symbol = ['♠', '♥', '♦', '♣']

class Card:
    def __init__(self, nbr):
        self.value = (nbr%13)%4 +1
        self.symbol = symbol[(nbr//13)%4]

    def prefix(self):
        match self.value:
            case 1: return 'A'
            case 11: return 'J'
            case 12: return 'Q'
            case 13: return 'K'
            case _: return str(self.value)

    def __str__(self):
        return self.prefix() + self.symbol

    def __repr__(self):
        return self.prefix() + self.symbol

    def __add__(self, other):
        return self.value + other.value

    def __int__(self):
        return self.value


class Deck(object):
    def __init__(self, nbr_of_decks =1):
        self.deck = [i for i in range(52*nbr_of_decks)]
        self.nbr_of_decks = nbr_of_decks
        random.seed(time.time())

    def reset_deck(self):
        self.deck = [i for i in range(52*self.nbr_of_decks)]
        random.seed(time.time())

    def shuffle(self):
        random.shuffle(self.deck)

    def draw_next(self):
        return self.deck.pop(0)

    def draw(self):
        random.seed(time.time())
        card_nbr = random.choice(self.deck)
        self.deck.remove(card_nbr)
        return Card(card_nbr)

