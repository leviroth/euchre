from random import shuffle

class Deck():
    suits = {"C", "D", "H", "S"}
    colors = {"C": "black", "S": "black", "D": "red", "H": "red"}
    ranks = ["9", "10", "J", "Q", "K", "A"]

    def __init__(self):
        self.cards = {Card(rank, suit) for suit in self.suits for rank in self.ranks}
        self.reset()

    def draw(self):
        return self.remaining.pop()

    def shuffle(self):
        shuffle(self.remaining)

    def reset(self):
        self.remaining = list(self.cards)
        shuffle(self.remaining)

class Card():
    suitNames = {"C": "Clubs", "D": "Diamonds", "H": "Hearts", "S": "Spades"}
    rankNames = {"9": "9", "10": "10", "J": "Jack", "Q": "Queen", "K": "King", "A": "Ace"}

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

    def __hash__(self):
        return (self.rank, self.suit).__hash__()

    def __str__(self):
        return Card.rankNames[self.rank] + " of " + Card.suitNames[self.suit]

class Table():
    def __init__(self):
        self.players = [Player() for x in range(4)]
        self.dealer = players[0]
        self.deck = Deck()
        self.deal()

    def deal(self):
        for player in self.players:
            player.hand = {self.deck.draw() for _ in range(5)}

        self.upCard = self.deck.draw()
        self.phase = "bid1"

    def suit(card):
        if card.rank == "J" and Deck.colors[card.suit] == Deck.colors[self.trump]:
            return self.trump
        else:
            return card.suit

    def matchSuit(a, b):
        return suit(a) == suit(b)

    def trickCompare(a, b):
        if suit(a) == self.trump and suit(b) != self.trump:
            return False

class Hand():
    pass


class Trick():
    def __init__(self, hand):
        self.hand = hand
        self.trump = self.hand.trump
        self.cards = []

    def relativeSuit(self, card):
        if card.rank == "J" and Deck.colors[card.suit] == \
                Deck.colors[self.trump]:
            return self.trump
        else:
            return card.suit

    def following(self, card):
        if self.cards == []:
            return True
        else:
            return self.relativeSuit(card) == \
                    self.relativeSuit(self.cards[0][0])

    def relativeRank(self, card):
        if self.relativeSuit(card) == self.trump:
            fst = 2
        elif self.relativeSuit(card) == \
                self.relativeSuit(self.cards[0][0]):
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
        return max(self.cards, key=lambda x: self.relativeRank(x[0]))

    def play(self, card, player):
        self.cards.append((card, player))
        if len(self.cards) == 4:
            self.hand.tally(self.winner()[1])


class Player():
    def requireTurn(move):
        def _move(self, *args, **kwargs):
            if self is not t.turn:
                raise TurnError("Not your turn", t.turn)
            # if self.phase != t.phase:
            #     raise TurnError("Wrong phase")

        return _move

    def __init__(self, t):
        self.t = t

    @requireTurn
    def bidCall(self, suit=None, alone=False):
        if suit is None:
            if table.phase != "bid1":
                raise ValueError("We need a suit for this phase")
            table.dealer.pickUp(self.upCard)
            table.trumpSuit = self.upCard.suit

        else:
            if table.phase != "bid2":
                raise ValueError("You can't choose a suit in this phase")
            if suit == table.upCard.suit:
                raise ValueError("That suit was turned down")
            table.trumpSuit = suit

        if alone:
            table.loner(self)
        table.startRound()

    @requireTurn
    def bidPass(self):
        if table.dealer is self and table.phase == "bid2":
            raise ValueError("Screw the dealer!")
        else:
            table.passBid()

    @requireTurn
    def playCard(self, card):
        if not t.matchSuit(card, table.led) \
                and t.suit(table.led) in [t.suit(c) for c in self.hand]:
            raise ValueError("Must follow suit")
        else:
            self.hand.remove(card)
            table.play(card, self)

    def chooseCard(self):
        while True:
            card = self.ui.chooseCard()
            if card in self.hand:
                break
            self.ui.complain("Card not in hand")
        return card

    def pickUp(self, upCard):
        hand.add(upCard)
        hand.remove(self.chooseCard())
