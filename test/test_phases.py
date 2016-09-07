import unittest
from unittest.mock import *
from euchre.objects import Suit
from euchre.phases import *


class PhaseTest(unittest.TestCase):
    def setUp(self):
        self.table = Mock()
        self.hand = Mock()
        self.players = [Mock() for _ in range(4)]
        for i in range(4):
            self.players[i].left = self.players[(i + 1) % 4]
            self.players[i].partner = self.players[(i + 2) % 4]
            self.players[i].team = i % 2


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
