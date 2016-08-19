import unittest
from euchre import objects

class CardTest(unittest.TestCase):
    def test_valid_cards(self):
        self.assertRaises(ValueError, objects.Card, "10", "F")
        self.assertRaises(ValueError, objects.Card, "8", "F")
        try:
            objects.Card("10", "C")
        except ValueError:
            self.fail("Card(\"10\", \"C\") raised ValueError")

class DeckTest(unittest.TestCase):
    def setUp(self):
        self.deck = objects.Deck()

    def test_deck(self):
        self.assertIn(objects.Card("10", "C"), self.deck.cards)

    def test_pop(self):
        myCard = self.deck.draw()
        self.assertIn(myCard, self.deck.cards)
        self.assertNotIn(myCard, self.deck.remaining)
