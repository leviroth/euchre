import unittest
from unittest.mock import *
from euchre.objects import *


class CardTest(unittest.TestCase):
    def test_valid_cards(self):
        self.assertRaises(ValueError, Card, "10", "F")
        self.assertRaises(ValueError, Card, "8", "F")
        try:
            Card("10", "C")
        except ValueError:
            self.fail("Card(\"10\", \"C\") raised ValueError")

    def test_eq(self):
        self.assertTrue(Card("J", "H"), Card("j", "h"))


class DeckTest(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()

    def test_deck(self):
        self.assertIn(Card("10", "C"), self.deck.cards)

    def test_draw(self):
        myCard = self.deck.draw()
        self.assertIn(myCard, self.deck.cards)
        self.assertNotIn(myCard, self.deck.remaining)


class TrickTest(unittest.TestCase):
    @patch('euchre.objects.Hand')
    @patch('euchre.objects.Player')
    def setUp(self, PlayerMock, HandMock):
        self.h = Hand()
        Hand.tally = Mock()
        self.h.trump = "H"
        self.t = Trick(self.h)
        self.p = Player(self.t)
        self.p2 = Player(self.t)

    def test_relativeSuit(self):
        self.assertTrue(self.t.following(Card("10", "S")))
        self.t.play(Card("J", "H"), self.p)
        self.assertEqual("H", self.t.relativeSuit(Card("J", "D")))
        self.assertEqual("H", self.t.relativeSuit(Card("Q", "H")))
        self.assertEqual("D", self.t.relativeSuit(Card("Q", "D")))
        self.assertEqual("S", self.t.relativeSuit(Card("10", "S")))
        self.assertTrue(self.t.following(Card("J", "D")))
        self.assertFalse(self.t.following(Card("J", "C")))

    def test_relativeRank(self):
        self.t.play(Card("J", "H"), self.p)
        self.assertEqual((2, 11), self.t.relativeRank(Card("J", "H")))
        self.assertEqual((2, 10), self.t.relativeRank(Card("J", "D")))
        self.assertEqual((0, 3), self.t.relativeRank(Card("Q", "C")))

    def test_play(self):
        self.t.play(Card("10", "C"), self.p)
        self.t.play(Card("J", "C"), self.p2)
        self.assertEqual(self.t.winner()[1], self.p2)
        self.t.play(Card("10", "H"), self.p)
        self.assertFalse(self.h.tally.called)
        self.assertEqual(self.t.winner()[1], self.p)
        self.t.play(Card("J", "D"), self.p2)
        self.assertEqual(self.t.winner()[1], self.p2)
        self.assertTrue(self.h.tally.called)
