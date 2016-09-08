import unittest
from unittest.mock import *
from euchre.objects import *
from euchre.exceptions import *


class DeckTest(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()

    def test_deck(self):
        self.assertIn(Card(Rank.ten, Suit.clubs), self.deck.cards)

    def test_colors(self):
        self.assertEqual(Color.red, Suit.diamonds.color)
        self.assertEqual(Color.red, Suit.hearts.color)
        self.assertEqual(Color.black, Suit.spades.color)
        self.assertEqual(Color.black, Suit.clubs.color)

    def test_draw(self):
        myCard = self.deck.draw()
        self.assertIn(myCard, self.deck.cards)
        self.assertNotIn(myCard, self.deck.remaining)


class TableTest(unittest.TestCase):
    def setUp(self):
        self.table = Table()

    def test_hasPriority(self):
        self.assertFalse(self.table.hasPriority(Mock(), Mock()))

    @patch('euchre.objects.Table.win')
    def test_updateScore(self, winMock):
        self.table.dealCycle = MagicMock()
        for i in range(10):
            self.table.updateScore(i % 2, 1)
        self.assertEqual(5, self.table.points[0])
        self.assertEqual(5, self.table.points[1])
        self.assertFalse(self.table.won)
        self.assertFalse(winMock.called)

        for i in range(9):
            self.table.updateScore(i % 2, 1)
        self.assertEqual(10, self.table.points[0])
        self.assertEqual(9, self.table.points[1])
        self.assertTrue(self.table.won)
        self.assertTrue(winMock.called)
