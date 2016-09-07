import unittest
from unittest.mock import *
from euchre.objects import Suit
from euchre.phases import *


class PlayTest(unittest.TestCase):
    def setUp(self):
        self.table = Mock()
        self.players = [Mock() for _ in range(4)]
        for i in range(4):
            self.players[i].left = self.players[(i + 1) % 4]
            self.players[i].partner = self.players[(i + 2) % 4]
            self.players[i].team = i % 2
        self.table.players = dict(enumerate(self.players))


class PhaseTest(PlayTest):
    def setUp(self):
        super().setUp()
        self.hand = Mock()
        self.hand.dealer = self.players[0]


class BidPhaseTest(PhaseTest):
    @patch('euchre.phases.Bid2Phase')
    def test_Bid1Phase(self, BidMock):
        self.phase = Bid1Phase(self.hand)
        self.phase.passTurn()
        self.phase.passTurn()
        self.phase.passTurn()
        self.assertFalse(BidMock.called)
        self.phase.passTurn()
        self.assertTrue(BidMock.called)

    def test_Bid2Phase(self):
        self.phase = Bid2Phase(self.hand)
        self.phase.passTurn()
        self.phase.passTurn()
        self.phase.passTurn()
        self.assertRaises(ValueError, self.phase.passTurn)


class PlayPhaseTest(PhaseTest):
    def setUp(self):
        super().setUp()
        self.hand.table = self.table

    @patch('euchre.phases.PlayPhase.scoreRound')
    def test_trickWon(self, ScoreMock):
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[0], False)
        self.phase.tricksTaken = {0: 2, 1: 1}
        self.phase.trickWon(self.players[0])
        self.assertFalse(ScoreMock.called)
        self.phase.trickWon(self.players[1])
        self.assertTrue(ScoreMock.called)

    def test_scoreRound(self):
        calls = []

        # Team 0 wins
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[0], False)
        self.phase.tricksTaken = {0: 3, 1: 2}
        self.phase.scoreRound()
        calls.append((0, 1))

        # Team 1 wins
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[1], False)
        self.phase.tricksTaken = {0: 1, 1: 4}
        self.phase.scoreRound()
        calls.append((1, 1))

        # Team 0 euchered
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[0], False)
        self.phase.tricksTaken = {0: 2, 1: 3}
        self.phase.scoreRound()
        calls.append((1, 2))

        # Team 0 wins, march
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[0], False)
        self.phase.tricksTaken = {0: 5, 1: 0}
        self.phase.scoreRound()
        calls.append((0, 2))

        # Team 0 wins alone, no march
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[0], True)
        self.phase.tricksTaken = {0: 4, 1: 1}
        self.phase.scoreRound()
        calls.append((0, 1))

        # Team 0 wins, march + alone
        self.phase = PlayPhase(self.hand, Suit.spades,
                               self.players[0], True)
        self.phase.tricksTaken = {0: 5, 1: 0}
        self.phase.scoreRound()
        calls.append((0, 4))

        self.table.updateScore.assert_has_calls([call(*x) for x in calls])


class DiscardPhaseTest(PhaseTest):
    def setUp(self):
        super().setUp()
        self.phase = DiscardPhase(self.hand, self.players[1], False)

    def test_run(self):
        self.phase.run()
        self.assertTrue(self.hand.dealer.hand.add.called)

    @patch('euchre.phases.PlayPhase')
    def test_proceed(self, PPMock):
        self.phase.proceed()
        self.hand.runPhase.assert_called_with(
            PPMock(self.phase.hand,
                   self.phase.hand.upCard.suit, self.players[1], False)
        )


class HandTest(PlayTest):
    def setUp(self):
        super().setUp()
        self.hand = Hand(self.table, self.players[0])

    def test_hasPriority(self):
        self.assertFalse(self.hand.hasPriority(self.players[1], Bid1Phase))
        self.hand.run()
        self.assertTrue(self.hand.hasPriority(self.players[1], Bid1Phase))

    def test_deal(self):
        self.hand.deal()

        for player in self.players:
            self.assertEqual(5, len(player.hand))
        self.assertIsNotNone(self.hand.upCard)
