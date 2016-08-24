from random import shuffle
import itertools


class Deck():
    suits = {"C", "D", "H", "S"}
    colors = {"C": "black", "S": "black", "D": "red", "H": "red"}
    ranks = ["9", "10", "J", "Q", "K", "A"]

    def __init__(self):
        self.cards = {Card(rank, suit) for suit in self.suits
                      for rank in self.ranks}
        self.reset()

    def draw(self):
        return self.remaining.pop()

    def shuffle(self):
        shuffle(self.remaining)

    def reset(self):
        self.remaining = list(self.cards)
        self.shuffle()


class Card():
    suitNames = {"C": "Clubs", "D": "Diamonds", "H": "Hearts", "S": "Spades"}
    rankNames = {"9": "9", "10": "10", "J": "Jack", "Q": "Queen",
                 "K": "King", "A": "Ace"}

    def __init__(self, rank, suit):
        suit = suit.upper()
        rank = rank.upper()

        if suit not in Deck.suits:
            raise ValueError('That is not a suit')
        if rank not in Deck.ranks:
            raise ValueError('That is not a rank')
        self.suit = suit
        self.rank = rank

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank

    def __lt__(self, other):
        # if self.suit == other.suit:
        #     return self.rank < other.rank
        # return self.suit < other.suit
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __hash__(self):
        return (self.rank, self.suit).__hash__()

    def __str__(self):
        return Card.rankNames[self.rank] + " of " + Card.suitNames[self.suit]


class Table():
    def __init__(self):
        self.players = [Player(self, x) for x in range(4)]
        for i in range(4):
            self.players[i].left = self.players[(i + 1) % 4]
            self.players[i].partner = self.players[(i + 2) % 4]
        self.dealer = self.players[0]
        self.deck = Deck()
        self.points = {x: 0 for x in range(2)}
        self.ui = GameUI(self)
        self.won = False

    def run(self):
        cycle = itertools.cycle(self.players)
        while not self.won:
            dealer = next(cycle)
            Hand(self, dealer).run()

    def itPlayers(self, first, excluded={}):
        for i in range(4):
            p = self.players[(first + i) % 4]
            if p not in excluded:
                yield p

    def win(self, team):
        self.ui.win(team)

    def updateScore(self, team, points):
        self.points[team] += points
        if self.points[team] >= 10:
            self.won = True
            self.win(team)


class Hand():
    def __init__(self, table, dealer):
        self.table = table
        self.dealer = dealer
        self.table.deck.reset()
        self.tricksTaken = {x: 0 for x in range(2)}
        self.deal()

    def run(self):
        if not self.bid1():
            if not self.bid2():
                return
        self.playRound()
        self.scoreRound()

    def deal(self):
        for player in self.table.players:
            player.hand = {self.table.deck.draw() for _ in range(5)}

        self.upCard = self.table.deck.draw()

    def bid1(self):
        for player in self.table.itPlayers(self.dealer.left.n):
            bid = player.bid1(self.upCard)
            if bid['call']:
                self.configureRound(player, self.upCard.suit, bid['alone'])
                if self.dealer is not self.out:
                    self.dealer.pickUp(self.upCard)
                return True

        return False

    def bid2(self):
        for player in self.table.itPlayers(self.dealer.left.n):
            bid = player.bid2(self.upCard.suit)
            if bid['call']:
                self.configureRound(player, bid['suit'], bid['alone'])
                return True

        return False

    def configureRound(self, player, suit, alone):
        self.trump = suit
        self.loner = alone
        self.maker = player.team
        if self.loner:
            self.leader = player.left
            self.out = player.partner
        else:
            self.leader = self.dealer.left
            self.out = None

    def playRound(self):
        leader = self.leader
        for i in range(5):
            sequence = self.table.itPlayers(leader.n, excluded={self.out})
            trick = Trick(self, leader)
            winner = trick.play(sequence)
            self.tricksTaken[winner.team] += 1
            leader = winner

    def scoreRound(self):
        winningTeam = max(self.tricksTaken,
                          key=lambda x: self.tricksTaken[x])
        tricksTaken = self.tricksTaken[winningTeam]

        if winningTeam != self.maker:
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


class Trick():
    class Play():
        def __init__(self, card, player):
            self.card = card
            self.player = player

    def __init__(self, hand, leader):
        self.hand = hand
        self.trump = self.hand.trump
        self.cards = []
        self.leader = leader

    def relativeSuit(self, card):
        if card.rank == "J" and Deck.colors[card.suit] == \
                Deck.colors[self.trump]:
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

        if fst == 2 and card.rank == "J":
            if card.suit == self.trump:
                snd = 11
            else:
                snd = 10
        else:
            snd = Deck.ranks.index(card.rank)

        return (fst, snd)

    def winner(self):
        return max(self.cards, key=lambda x: self.relativeRank(x.card))

    def play(self, sequence):
        for player in sequence:
            self.cards.append(self.Play(player.playCard(self), player))
        return self.winner().player


class Player():
    def __init__(self, t, n):
        self.table = t
        self.n = n
        self.team = n % 2
        self.ui = UserInterface(self)

    def __str__(self):
        return "Player {}".format(self.n)

    def __repr__(self):
        return "Player " + str(self.n)

    def __hash__(self):
        return self.n.__hash__()

    def bid1(self, upCard):
        return self.ui.bid1(upCard)

    def bid2(self, excludedSuit):
        return self.ui.bid2(excludedSuit)

    def playCard(self, trick):
        while True:
            card = self.chooseCard()
            if trick.following(card) or trick.ledSuit() not in \
                    [trick.relativeSuit(c) for c in self.hand]:
                break
            self.ui.complain("Must follow suit")

        self.hand.remove(card)
        return card

    def chooseCard(self):
        while True:
            card = self.ui.chooseCard()
            if card in self.hand:
                break
            self.ui.complain("Card not in hand")
        return card

    def pickUp(self, upCard):
        self.hand.add(upCard)
        self.hand.remove(self.chooseCard())


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
