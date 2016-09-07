import unittest
from unittest.mock import *
from euchre.objects import Suit, Card, Rank
from euchre.phases import Trick
from test.test_phases import PhaseTest


class TrickTest(PhaseTest):
    def setUp(self):
        super().setUp()
        self.phase = Mock()
        self.phase.trump = Suit.spades
        self.trick = Trick(self.phase, self.players[0])
        self.trick.run()

    @patch('euchre.phases.Phase', False)
    def test_relativeSuit(self):
        self.assertTrue(self.trick.following(Card.fromStrs("10", "H")))
        self.trick.play(self.players[0], Card(Rank.nine, Suit.spades))
        self.assertEqual(Suit.spades,
                         self.trick.relativeSuit(Card.fromStrs("J", "C")))
        self.assertEqual(Suit.spades,
                         self.trick.relativeSuit(Card.fromStrs("Q", "S")))
        self.assertEqual(Suit.clubs,
                         self.trick.relativeSuit(Card.fromStrs("Q", "C")))
        self.assertEqual(Suit.spades,
                         self.trick.relativeSuit(Card.fromStrs("10", "S")))
        self.assertTrue(self.trick.following(Card.fromStrs("J", "C")))
        self.assertFalse(self.trick.following(Card.fromStrs("J", "H")))

    @patch('euchre.phases.Trick.ledSuit', lambda x: Suit.clubs)
    def test_relativeRank(self):
        self.assertEqual((2, 21),
                         self.trick.relativeRank(Card.fromStrs("J", "S")))
        self.assertEqual((2, 20),
                         self.trick.relativeRank(Card.fromStrs("J", "C")))
        self.assertEqual((1, 9),
                         self.trick.relativeRank(Card.fromStrs("9", "C")))
        self.assertEqual((0, 12),
                         self.trick.relativeRank(Card.fromStrs("Q", "D")))

    @patch('euchre.phases.Trick.winner')
    def test_play(self, WinnerMock):
        self.trick.play(self.players[0], Card(Rank.jack, Suit.diamonds))
        self.assertEqual(self.trick.Play(Card(Rank.jack,
                                              Suit.diamonds),
                                         self.players[0]),
                         self.trick.cards[0])
        self.assertFalse(self.phase.trickWon.called)
        self.trick.play(self.players[1], Card(Rank.jack, Suit.diamonds))
        self.trick.play(self.players[2], Card(Rank.jack, Suit.diamonds))
        self.trick.play(self.players[3], Card(Rank.jack, Suit.diamonds))
        self.assertEqual(self.trick.leader, self.trick.turn)
        self.phase.trickWon.assert_called_once_with(WinnerMock())

    # We could patch relativeRank here
    def test_winner(self):
        self.trick.cards = (
            Trick.Play(Card(Rank.queen, Suit.clubs), self.players[0]),
            Trick.Play(Card(Rank.ace, Suit.diamonds), self.players[1]),
            Trick.Play(Card(Rank.nine, Suit.spades), self.players[2]),
            Trick.Play(Card(Rank.ace, Suit.clubs), self.players[3])
        )
        self.assertEqual(self.players[2], self.trick.winner())
