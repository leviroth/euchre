from random import shuffle

class Deck():
    suits = {"C", "D", "H", "S"}
    ranks = {"9", "10", "J", "Q", "K", "A"}

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
        self.players = [Player() for x in xrange(4)]
        self.dealer = players[0]
        self.deck = Deck()
        self.deal()

    def deal(self):
        for player in self.players:
            player.hand = {self.deck.draw() for _ in xrange(5)}

        self.upCard = self.deck.draw()
        self.phase = "bid1"

class Player():
    def requireTurn(self, move):
        def _move(self, *args, **kwargs):
            if self is not t.turn:
                raise TurnError("Not your turn", t.turn)
            # if self.phase != t.phase:
            #     raise TurnError("Wrong phase")

        return move

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
        if not t.matchSuit(card, led):
            raise ValueError("Must follow suit")
        else:
            self.hand.remove(card)
            table.play(card)

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
