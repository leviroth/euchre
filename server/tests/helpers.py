from euchre.objects import Suit


def cardKey(x):
    suitKey = {Suit.clubs: 1,
               Suit.diamonds: 2,
               Suit.hearts: 3,
               Suit.spades: 4
               }
    return (suitKey[x.suit], int(x.rank))


def cardSort(deck):
    deck.remaining.sort(key=cardKey)
