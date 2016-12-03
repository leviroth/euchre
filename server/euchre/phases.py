import euchre


class Phase():
    def __init__(self, hand):
        self.hand = hand

    def broadcast(self, message):
        self.hand.broadcast(message)

    def run(self):
        pass


class BidPhase(Phase):
    def __init__(self, hand):
        super().__init__(hand)
        self.upCard = self.hand.upCard
        self.dealer = self.hand.dealer
        self._turn = self.dealer.left

    @property
    def turn(self):
        return self._turn


class Bid1Phase(BidPhase):
    def __str__(self):
        return "bid1"

    def call(self, player, alone):
        self.hand.runPhase(DiscardPhase(self.hand, player, alone))

    def passTurn(self):
        if self.turn == self.dealer:
            self.hand.runPhase(Bid2Phase(self.hand))
        else:
            self._turn = self._turn.left


class Bid2Phase(BidPhase):
    def __str__(self):
        return "bid2"

    def call(self, player, suit, alone):
        self.hand.runPhase(PlayPhase(self.hand, suit, player, alone))

    def passTurn(self):
        if self.turn == self.dealer:
            raise ValueError("Dealer is stuck")
        else:
            self._turn = self._turn.left


class DiscardPhase(Phase):
    def __init__(self, hand, player, alone):
        super().__init__(hand)
        self.maker = player
        self.alone = alone

    def __str__(self):
        return "discard"

    def run(self):
        self.hand.dealer.hand.add(self.hand.upCard)

    @property
    def turn(self):
        return self.hand.dealer

    def proceed(self):
        self.hand.runPhase(PlayPhase(self.hand, self.hand.upCard.suit,
                                     self.maker, self.alone))


class PlayPhase(Phase):
    def __init__(self, hand, trump, maker, alone):
        super().__init__(hand)
        self.trump = trump
        self.alone = alone
        self.maker = maker
        if self.alone:
            self.leader = self.maker.left
            self.out = self.maker.partner
        else:
            self.leader = self.hand.dealer.left
            self.out = None
        self.tricksTaken = {x: 0 for x in range(2)}

    def __str__(self):
        return "play"

    def run(self):
        self.trick = Trick(self, self.leader)
        self.trick.run()

    @property
    def turn(self):
        return self.trick.turn

    def trickWon(self, winner):
        self.tricksTaken[winner.team] += 1
        self.hand.broadcast(str(winner) + "won the trick")
        if sum(self.tricksTaken.values()) == 5:
            self.scoreRound()
        else:
            self.trick = Trick(self, winner)
            self.trick.run()

    def scoreRound(self):
        winningTeam, tricksTaken = max(self.tricksTaken.items(),
                                       key=lambda x: x[1])

        if winningTeam != self.maker.team:
            points = 2
        else:
            if tricksTaken == 5:
                if self.alone:
                    points = 4
                else:
                    points = 2
            else:
                points = 1

        self.hand.table.updateScore(winningTeam, points)


class Trick():
    class Play():
        def __init__(self, card, player):
            self.card = card
            self.player = player

        def __eq__(self, other):
            return self.card == other.card and self.player == other.player

    def __init__(self, phase, leader):
        self.phase = phase
        self.trump = self.phase.trump
        self.cards = []
        self.leader = leader

    def run(self):
        self._turn = self.leader

    @property
    def turn(self):
        return self._turn

    def passTurn(self):
        self._turn = self._turn.left
        if self._turn is self.phase.out:
            self._turn = self._turn.left

    def relativeSuit(self, card):
        if card.rank == euchre.objects.Rank.jack and card.color == \
                self.trump.color:
            return self.trump
        else:
            return card.suit

    @property
    def ledSuit(self):
        return self.relativeSuit(self.cards[0].card)

    def following(self, card):
        if self.cards == []:
            return True
        else:
            return self.relativeSuit(card) == self.ledSuit

    def relativeRank(self, card):
        if self.relativeSuit(card) == self.trump:
            fst = 2
        elif self.relativeSuit(card) == self.ledSuit:
            fst = 1
        else:
            fst = 0

        if fst == 2 and card.rank == euchre.objects.Rank.jack:
            if card.suit == self.trump:
                snd = 21
            else:
                snd = 20
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


class Hand():
    def __init__(self, table, dealer):
        self.table = table
        self.dealer = dealer
        self.deck = euchre.objects.Deck()

    def broadcast(self, message):
        self.table.broadcast(message)

    def hasPriority(self, player, phase):
        try:
            return self.phase.turn is player \
                    and self.phase.__class__ == phase
        except AttributeError:
            return False

    def runPhase(self, phase):
        self.phase = phase
        self.phase.run()

    def deal(self):
        self.deck.reset()
        for player in self.table.players.values():
            player.hand = {self.deck.draw() for _ in range(5)}
        self.upCard = self.deck.draw()

    def run(self):
        self.deal()
        self.runPhase(Bid1Phase(self))
