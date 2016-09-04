from random import shuffle
from enum import Enum, unique
from exceptions import *
import itertools
from functools import wraps


Color = Enum('Color', 'red black')
# Phase = Enum('Phase', 'bid1 bid2 lay pickup')


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


class Phase():
    def broadcast(self, message):
        self.hand.broadcast(message)


class BidPhase(Phase):
    def __init__(self, hand, dealer):
        self.hand = hand
        self.upCard = self.hand.upCard
        self.dealer = dealer
        self._turn = dealer.left


class Bid1Phase(BidPhase):
    def turn(self):
        return self._turn

    def call(self, player, alone):
        self.hand.phase = DiscardPhase(self.hand, player, alone)

    def passTurn(self):
        if self.turn == self.dealer:
            self.hand.phase = Bid2Phase(self.hand, self.dealer)
        else:
            self.turn = self.turn.left


class Bid2Phase(BidPhase):
    def turn(self):
        return self._turn

    def call(self, player, suit, alone):
        self.hand.phase = PlayPhase(self.hand, suit, player, alone)

    def passTurn(self):
        if self.turn == self.dealer:
            raise ValueError("Dealer is stuck")
        else:
            self.turn = self.turn.left


class DiscardPhase(Phase):
    def __init__(self, hand, player, alone):
        self.hand = hand
        self.maker = player
        self.alone = alone
        self.hand.dealer.hand.add(self.hand.upCard)

    def turn(self):
        return self.hand.dealer

    def proceed(self):
        self.hand.phase = PlayPhase(self.hand, self.upCard.suit, self.maker,
                                    self.loner)


class PlayPhase(Phase):
    def __init__(self, hand, trump, maker, loner):
        self.hand = hand
        self.trump = suit
        self.loner = loner
        self.maker = maker
        if self.loner:
            leader = self.maker.left
            self.out = self.maker.partner
        else:
            leader = self.hand.dealer.left
            self.out = None
        self.tricksTaken = {x: 0 for x in range(2)}

        self.trick = Trick(self, leader)
        self.trick.run()

    def turn(self):
        return self.trick._turn

    def trickWon(self, winner):
        self.tricksTaken[winner.team] += 1
        self.table.broadcast(str(winner) + "won the trick")
        if sum(self.tricksTaken.values()) == 5:
            self.scoreRound()
        else:
            self.trick = Trick(self, winner)
            self.trick.run()

    def scoreRound(self):
        winningTeam = max(self.tricksTaken,
                          key=lambda x: self.tricksTaken[x])
        tricksTaken = self.tricksTaken[winningTeam]

        if winningTeam != self.maker.team:
            points = 2
        else:
            if tricksTaken == 5:
                if self.loner:
                    points = 4
                else:
                    points = 2
            else:
                points = 1

        self.table.updateScore(winningTeam, points)


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

    def __init__(self, protocol):
        self.protocol = protocol
        self.name = "<unnamed>"

    def __str__(self):
        return self.name

    # def __repr__(self):
    #     return "Player: " + str(self)

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

    @requireTurn(Bid1Phase)
    def bid1(self, call, alone):
        if call:
            self.table.hand.phase.call(self, alone)
        else:
            self.table.hand.passTurn()

    @requireTurn(Bid2Phase)
    def bid2(self, call, alone, suit=None):
        if suit is None:
            raise ValueError("Must choose suit")
        if suit is self.table.hand.upCard.suit:
            raise ValueError("Suit was turned down")
        if call:
            self.table.hand.phase.call(self, alone, suit)
        else:
            self.table.hand.passTurn()

    @requireTurn(PlayPhase)
    def playCard(self, card):
        trick = self.table.currentTrick()
        if card not in self.hand:
            raise ValueError("Card not in hand")
        if not trick.following(card) \
            and trick.ledSuit() not in \
                [trick.relativeSuit(c) for c in self.hand]:
            raise ValueError("May not renege")

        self.hand.remove(card)
        self.table.play(self, card)

    @requireTurn(DiscardPhase)
    def pickUp(self, card):
        if card not in self.hand:
            raise ValueError("You don't have that card")
        self.hand.remove(card)
        self.table.hand.phase.proceed()


class Table():
    def __init__(self):
        self.players = {}
        self.deck = Deck()
        self.points = {x: 0 for x in range(2)}
        # self.ui = GameUI(self)
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
        except NameError:
            return False

    def currentTrick(self):
        return self.hand.phase.trick

    def begin(self):
        for i in range(4):
            self.players[i].left = self.players[(i + 1) % 4]
            self.players[i].partner = self.players[(i + 2) % 4]
        self.dealCycle = itertools.cycle(self.players.values())
        self.nextHand()

    def nextHand(self):
        self.hand = Hand(self, next(self.dealCycle))
        self.hand.run()

#     def itPlayers(self, first, excluded={}):
#         """Not currently in use"""
#         startIndex = self.players.index(first)
#         for i in range(4):
#             p = self.players[(startIndex + i) % 4]
#             if p not in excluded:
#                 yield p

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


class Hand():
    def __init__(self, table, dealer):
        self.table = table
        self.dealer = dealer

    def broadcast(self, message):
        self.table.broadcast(message)

    def hasPriority(self, player, phase):
        try:
            return self.phase.turn() == player \
                    and self.phase.__class__ == phase
        except NameError:
            return False

    def passTurn(self):
        self.phase.passTurn()

    def run(self):
        self.table.deck.reset()
        for player in self.table.players.values():
            player.hand = {self.table.deck.draw() for _ in range(5)}
        self.upCard = self.table.deck.draw()
        self.phase = Bid1Phase(self, self.dealer)

#     def call1(self, player, alone):
#         self.configureRound(player, self.upCard.suit, alone)
#         self.table.server.updateRound()
#         self.table.server.discardPrompt()
#         self.turn = self.leader

#     def call2(self, player, suit, alone):
#         self.configureRound(player, suit, alone)
#         self.turn = self.leader
#         self.table.server.updateRound()

    # def bid1(self):
    #     for player in self.table.itPlayers(self.dealer.left):
    #         bid = player.bid1(self.upCard)
    #         if bid['call']:
    #             self.configureRound(player, self.upCard.suit, bid['alone'])
    #             if self.dealer is not self.out:
    #                 self.dealer.pickUp(self.upCard)
    #             return True

    #     return False

#     def bid2(self):
#         for player in self.table.itPlayers(self.dealer.left):
#             bid = player.bid2(self.upCard.suit)
#             if bid['call']:
#                 self.configureRound(player, bid['suit'], bid['alone'])
#                 return True

#         return False

    # def configureRound(self, player, suit, alone):
    #     self.trump = suit
    #     self.loner = alone
    #     self.maker = player.team
    #     if self.loner:
    #         self.leader = player.left
    #         self.out = player.partner
    #     else:
    #         self.leader = self.dealer.left
    #         self.out = None
    #     self.phase = Phase.lay

#     def playRound(self):
#         leader = self.leader
#         for i in range(5):
#             sequence = self.table.itPlayers(leader, excluded={self.out})
#             trick = Trick(self, leader)
#             winner = trick.play(sequence)
#             self.tricksTaken[winner.team] += 1
#             leader = winner


class Trick():
    class Play():
        def __init__(self, card, player):
            self.card = card
            self.player = player

    def __init__(self, phase, leader):
        self.phase = phase
        self.trump = self.phase.trump
        self.cards = []
        self.leader = leader

    def run(self):
        self._turn = self.leader

    def passTurn(self):
        self._turn = self._turn.left
        if self._turn is self.phase.out:
            self._turn = self._turn.left

    def relativeSuit(self, card):
        if card.rank == Rank.jack and card.color == \
                self.trump.color:
            return self.trump
        else:
            return card.suit

    def ledSuit(self):
        return self.relativeSuit(self.cards[0].card)

    def following(self, card):
        if self.cards == []:
            return True
        else:
            return self.relativeSuit(card) == self.ledSuit()

    def relativeRank(self, card):
        if self.relativeSuit(card) == self.trump:
            fst = 2
        elif self.relativeSuit(card) == self.ledSuit():
            fst = 1
        else:
            fst = 0

        if fst == 2 and card.rank == Rank.jack:
            if card.suit == self.trump:
                snd = 11
            else:
                snd = 10
        else:
            snd = int(card.rank)

        return (fst, snd)

    def winner(self):
        return max(self.cards, key=lambda x: self.relativeRank(x.card)).player

    def play(self, player, card):
        self.cards.append(self.Play(card, player))
        self.passTurn()
        if self._turn is self.leader:
            self.phase.trickWon(self.winner())


class UserInterface():  # pragma: no cover
    def __init__(self, player):
        self.player = player

    def prompt(self, s):
        return input("[{}] {}".format(str(self.player), s))

    def printHand(self):
        print("\nHand:")
        for card in self.player.hand:
            print(card)

    def chooseCard(self):
        self.printHand()
        rank = self.prompt("Rank: ")
        suit = self.prompt("Suit: ")
        return Card(rank, suit)

    def bid1(self, upCard):
        print("Up Card: " + str(upCard))
        self.printHand()
        while True:
            call = self.prompt("Call? ")
            if call == "y" or call == "n":
                break

        result = {'call': True if call == "y" else False}
        if result['call']:
            while True:
                alone = self.prompt("Alone? ")
                if alone == "y" or alone == "n":
                    break
            result.update({'alone': True if alone == "y" else False})

        return result

    def bid2(self, excludedSuit):
        self.printHand()
        while True:
            call = self.prompt("Call? ")
            if call == "y" or call == "n":
                break

        result = {'call': True if call == "y" else False}
        if result['call']:
            while True:
                suit = self.prompt("Suit? ")
                if suit != excludedSuit:
                    break
                print("That suit was turned down.")
            result.update({'suit': suit})

            while True:
                alone = self.prompt("Alone? ")
                if alone == "y" or alone == "n":
                    break
            result.update({'alone': True if alone == "y" else False})

        return result

    def complain(self, msg):
        print(msg)


class GameUI():
    def __init__(self, table):
        self.table = table

    def win(self, team):
        print("Team {} wins!".format(team))

if __name__ == '__main__':
    t = Table()
    ps = [Player(n) for n in range(4)]
    for i, p in enumerate(ps):
        p.joinTable(t, i)
    t.begin()
