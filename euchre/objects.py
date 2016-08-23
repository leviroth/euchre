from random import shuffle


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
        shuffle(self.remaining)


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
        self.team = {p: p.n % 2 for p in self.players}
        self.dealer = self.players[0]
        self.deck = Deck()
        self.deal()

    def itPlayers(self, first):
        for i in range(4):
            yield self.players[(first + i) % 4]

    def deal(self):
        for player in self.players:
            player.hand = {self.deck.draw() for _ in range(5)}

        self.upCard = self.deck.draw()
        self.phase = "bid1"


class Hand():
    def __init__(self, trump, leader, maker, loner, table):
        self.table = table
        self.trump = trump
        self.leader = leader
        self.maker = maker
        self.loner = loner
        self.points = {p: 0 for p in set(self.table.team.values())}

    def playRound(self):
        leader = self.leader
        out = leader.left if self.loner else None
        for i in range(5):
            sequence = filter(lambda x: x != out,
                              self.table.itPlayers(leader.n))
            trick = Trick(self, leader)
            winner = trick.play(sequence)
            self.points[self.table.team[winner]] += 1
            leader = winner

        winningTeam = max(self.table.teams, key=lambda x: self.points[x])
        if winningTeam != self.table.team[self.maker]:
            self.table.points[winningTeam] += 2
        else:
            if self.points[winningTeam] == 5:
                if self.loner:
                    self.table.points[winningTeam] += 4
                else:
                    self.table.points[winningTeam] += 2
            else:
                self.table.points[winningTeam] += 1


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
    def requireTurn(move):
        def _move(self, *args, **kwargs):
            pass
            # if self is not t.turn:
            #     raise TurnError("Not your turn", t.turn)
            # if self.phase != t.phase:
            #     raise TurnError("Wrong phase")

        return _move

    def __init__(self, t, n):
        self.table = t
        self.n = n
        self.ui = UserInterface(self)

    def __str__(self):
        return str(self.n)

    def __repr__(self):
        return "Player " + str(self.n)

    def __hash__(self):
        return self.n.__hash__()

    @requireTurn
    def bidCall(self, suit=None, alone=False):
        if suit is None:
            if self.table.phase != "bid1":
                raise ValueError("We need a suit for this phase")
            self.table.dealer.pickUp(self.upCard)
            self.table.trumpSuit = self.upCard.suit

        else:
            if self.table.phase != "bid2":
                raise ValueError("You can't choose a suit in this phase")
            if suit == self.table.upCard.suit:
                raise ValueError("That suit was turned down")
            self.table.trumpSuit = suit

        if alone:
            self.table.loner(self)
        self.table.startRound()

    @requireTurn
    def bidPass(self):
        if self.table.dealer is self and self.table.phase == "bid2":
            raise ValueError("Screw the dealer!")
        else:
            self.table.passBid()

    # @requireTurn
    def playCard(self, trick):
        while True:
            card = self.ui.chooseCard()
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


class UserInterface():
    def __init__(self, player):
        self.player = player

    def chooseCard(self):
        while True:
            for card in self.player.hand:
                print(card)
            rank = input("Rank: ")
            suit = input("Suit: ")
            if card in self.player.hand:
                break
            self.complain("Card not in hand")

        return Card(rank, suit)

    def complain(self, msg):
        print(msg)

# t = Table()
# h = Hand(trump="H", leader=t.players[0],
#          maker=t.players[0], loner=True, table=t)
