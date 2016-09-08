from random import shuffle
from enum import Enum, unique
from euchre.exceptions import *
from euchre import phases
import itertools
from functools import wraps


Color = Enum('Color', 'red black')


@unique
class Suit(Enum):
    def __str__(self):
        return self.value

    clubs = "Clubs"
    diamonds = "Diamonds"
    hearts = "Hearts"
    spades = "Spades"

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
    jack = "Jack"
    queen = "Queen"
    king = "King"
    ace = "Ace"


class Deck():
    def __init__(self):
        self.cards = {Card(rank, suit) for suit in Suit
                      for rank in Rank}
        self.reset()

    def draw(self):
        return self.remaining.pop()

    def shuffle(self):
        shuffle(self.remaining)

    def reset(self):
        self.remaining = list(self.cards)
        self.shuffle()


class Card():
    def __init__(self, rank, suit):
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return (self.rank, self.suit).__hash__()

    def __str__(self):
        return str(self.rank) + " of " + str(self.suit)

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


class Player():
    def requireTurn(phase):
        def real_decorator(func):
            @wraps(func)
            def _func(self, *args, **kwargs):
                if not self.table.hasPriority(self, phase):
                    raise TurnError("It's not the time for that")
                return func(self, *args, **kwargs)
            return _func

        return real_decorator

    def __init__(self):
        self.name = "<unnamed>"

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.n.__hash__()

    def setName(self, name):
        self.name = name

    def joinTable(self, table, position):
        table.addPlayer(self, position)
        self.table = table
        self.position = position

    def leaveTable(self):
        self.table.removePlayer(self.position)

    @requireTurn(phases.Bid1Phase)
    def bid1(self, call, alone):
        if call:
            self.table.hand.phase.call(self, alone)
        else:
            self.table.hand.phase.passTurn()

    @requireTurn(phases.Bid2Phase)
    def bid2(self, call, alone, suit=None):
        if suit is None:
            raise ValueError("Must choose suit")
        if suit is self.table.hand.upCard.suit:
            raise ValueError("Suit was turned down")
        if call:
            self.table.hand.phase.call(self, alone, suit)
        else:
            self.table.hand.phase.passTurn()

    @requireTurn(phases.PlayPhase)
    def playCard(self, card):
        trick = self.table.currentTrick
        if card not in self.hand:
            raise ValueError("Card not in hand")
        if not trick.following(card) \
            and trick.ledSuit() not in \
                [trick.relativeSuit(c) for c in self.hand]:
            raise ValueError("May not renege")

        self.hand.remove(card)
        trick.play(self, card)

    @requireTurn(phases.DiscardPhase)
    def pickUp(self, card):
        if card not in self.hand:
            raise ValueError("You don't have that card")
        self.hand.remove(card)
        self.table.hand.phase.proceed()


class Table():
    def __init__(self):
        self.players = {}
        self.points = {x: 0 for x in range(2)}
        self.won = False

    def broadcast(self, message):
        print(message)

    def addPlayer(self, player, position):
        self.players[position] = player

    def removePlayer(self, position):
        self.pop(position)

    def hasPriority(self, *args, **kwargs):
        try:
            return self.hand.hasPriority(*args, **kwargs)
        except AttributeError:
            return False

    @property
    def currentTrick(self):
        return self.hand.phase.trick

    def run(self):
        for i in range(4):
            self.players[i].left = self.players[(i + 1) % 4]
            self.players[i].partner = self.players[(i + 2) % 4]
            self.players[i].team = i % 2
        self.dealCycle = itertools.cycle(self.players.values())
        self.nextHand()

    def nextHand(self):
        self.hand = phases.Hand(self, next(self.dealCycle))
        self.hand.run()

    def win(self, team):
        self.broadcast("Team {} won".format(team))

    def updateScore(self, team, points):
        self.points[team] += points
        self.broadcast("Team {} won the round and gets {} points"
                       .format(team, points))
        if self.points[team] >= 10:
            self.won = True
            self.win(team)
        else:
            self.nextHand()
