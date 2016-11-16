import unittest
import itertools
from unittest.mock import *
import euchre
from euchre.objects import *
from euchre.exceptions import *
from test.helpers import cardSort


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

    def test_run(self):
        self.players = [Mock() for _ in range(4)]
        for i, p in enumerate(self.players):
            self.table.addPlayer(p, i)

        self.table.run()
        for p, t in zip(self.players, itertools.cycle([0, 1])):
            self.assertIs(p, p.left.left.left.left)
            self.assertIs(p, p.partner.partner)
            self.assertEqual(t, p.team)

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


class PlayerTest(unittest.TestCase):
    @patch('euchre.objects.Deck.shuffle', new=cardSort)
    def setUp(self):
        self.player = Player()
        self.deck = Deck()
        self.table = Mock()
        self.player.joinTable(self.table, 0)
        self.player.hand = {self.deck.draw() for _ in range(5)}

    def test_requireTurn(self):
        @Player.requireTurn(euchre.phases.PlayPhase)
        def f(p, x):
            return x

        self.player.table.hasPriority.return_value = False
        self.assertRaises(TurnError, f, self.player, 5)

        self.player.table.hasPriority.return_value = True
        self.assertEqual(5, f(self.player, 5))

    def test_bid1(self):
        for alone in {True, False}:
            self.player.table.reset_mock()
            self.player.table.hasPriority.return_value = True
            with self.subTest(alone=alone):
                self.player.bid1(True, alone)
                self.player.table.hand.phase \
                    .call.assert_called_once_with(self.player, alone)

        self.player.table.reset_mock()
        self.player.table.hasPriority.return_value = True
        self.player.bid1(False, False)
        self.assertFalse(self.player.table.hand.phase.call.called)

    def test_bid2(self):
        self.player.table.hasPriority.return_value = True
        self.player.table.hand.upCard.suit = Suit.spades

        self.player.bid2(False, False, Suit.spades)
        self.player.bid2(False, False, Suit.diamonds)
        self.player.bid2(False, False)
        self.assertTrue(self.player.table.hand.phase.passTurn.called)
        self.assertFalse(self.player.table.hand.phase.call.called)

        self.player.table.reset_mock()
        self.player.table.hasPriority.return_value = True
        self.player.table.hand.upCard.suit = Suit.spades

        self.assertRaises(ValueError, self.player.bid2, True, False)
        self.assertRaises(ValueError, self.player.bid2, True, False,
                          Suit.spades)
        self.player.bid2(True, False, Suit.diamonds)
        self.assertTrue(self.player.table.hand.phase.call.called)
        self.assertFalse(self.player.table.hand.phase.passTurn.called)

    def test_playNotInHand(self):
        self.assertRaises(ValueError,
                          self.player.playCard,
                          Card(Rank.queen, Suit.diamonds))

    def test_playShortSuited(self):
        self.table.currentTrick.following.return_value = False
        self.table.currentTrick.relativeSuit.return_value = Suit.spades
        self.table.currentTrick.ledSuit = Suit.diamonds
        try:
            self.player.playCard(Card(Rank.ten, Suit.spades))
        except ValueError:
            self.fail("Complained when short suited")

    def test_playReneg(self):
        self.table.currentTrick.following.return_value = False
        self.table.currentTrick.relativeSuit.return_value = Suit.diamonds
        self.table.currentTrick.ledSuit = Suit.diamonds
        self.assertRaises(ValueError,
                          self.player.playCard,
                          Card(Rank.ten, Suit.spades))

    def test_playCard(self):
        self.table.currentTrick.following.return_value = True

        self.player.playCard(Card(Rank.ten, Suit.spades))
        self.assertNotIn(Card(Rank.ten, Suit.spades), self.player.hand)
        self.table.currentTrick.play.assert_called_once_with(
            self.player, Card(Rank.ten, Suit.spades)
        )

    def test_discard(self):
        self.assertRaises(ValueError, self.player.discard,
                          Card(Rank.ten, Suit.diamonds))

        self.player.discard(Card(Rank.ten, Suit.spades))
        self.assertNotIn(Card(Rank.ten, Suit.spades), self.player.hand)
        self.assertTrue(self.player.table.hand.phase.proceed.called)
