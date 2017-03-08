from random import shuffle
from enum import Enum, unique


Color = Enum('Color', 'red black')


@unique
class Suit(Enum):
    def __str__(self):
        return self.value

    clubs = "C"
    diamonds = "D"
    hearts = "H"
    spades = "S"

    @property
    def color(self):
        if self in {Suit.diamonds, Suit.hearts}:
            return Color.red
        else:
            return Color.black


@unique
class Rank(Enum):
    def __str__(self):
        return self.value

    def __int__(self):
        return {Rank.nine: 9,
                Rank.ten: 10,
                Rank.jack: 11,
                Rank.queen: 12,
                Rank.king: 13,
                Rank.ace: 14
                }[self]

    nine = "9"
    ten = "10"
    jack = "J"
    queen = "Q"
    king = "K"
    ace = "A"


class Card():
    def __init__(self, rank, suit):
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return (self.rank, self.suit).__hash__()

    def __repr__(self):
        return "Card({!r}, {!r})".format(self.rank, self.suit)

    def __str__(self):
        return str(self.rank) + "." + str(self.suit)

    @property
    def color(self):
        return self.suit.color

    @classmethod
    def fromStrs(cls, r, s):
        rank = {'9': Rank.nine,
                '10': Rank.ten,
                'J': Rank.jack,
                'Q': Rank.queen,
                'K': Rank.king,
                'A': Rank.ace
                }

        suit = {'C': Suit.clubs,
                'D': Suit.diamonds,
                'H': Suit.hearts,
                'S': Suit.spades,
                }

        return cls(rank[r], suit[s])


class Deck():
    cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    def __init__(self):
        self.remaining = self.cards.copy()

    def draw(self):
        return self.remaining.pop()

    def shuffle(self):
        shuffle(self.remaining)
