"""Test the Game class for correct implementation of game logic."""
import pytest

from euchre.exceptions import IllegalMoveException, OutOfTurnException
from euchre.game import (BidPhaseOne, BidPhaseTwo, DiscardPhase, Game,
                         PlayCardsPhase)
from euchre.objects import Card, Suit


def initial_game_state():
    hand_strs = ["A.S K.S J.S Q.H 9.D",
                 "A.C K.C J.C Q.D 9.H",
                 "A.H K.H J.H Q.C 9.C",
                 "A.D K.D J.D Q.S 9.S"]
    score = [0, 0]
    hands = [[Card.from_strs(*card_str.split(".")) for card_str in s.split()]
             for s in hand_strs]
    up_card = Card.from_strs("10", "D")
    initial_phase = BidPhaseOne(score, hands, 0, 1, up_card)
    return Game(initial_phase)


def test_enforce_turn():
    g = initial_game_state()
    with pytest.raises(OutOfTurnException):
        g.perform_move('pass_bid', 2)


def test_enforce_real_move():
    g = initial_game_state()
    with pytest.raises(RuntimeError):
        g.perform_move('nonexistent_move', 1)


def test_enforce_right_phase():
    g = initial_game_state()
    with pytest.raises(IllegalMoveException):
        g.perform_move('discard', 1, Card.from_strs("Q", "D"))


def test_pass():
    g = initial_game_state()
    next_state = g.perform_move('pass_bid', 1)
    assert next_state.turn == 2


def test_order_up():
    g = initial_game_state()
    next_state = g.perform_move('call', 1, False)
    dealer_hand = next_state.hands[0]
    assert isinstance(next_state, DiscardPhase)
    assert next_state.turn == 0
    assert next_state.trump == Suit.diamonds
    assert Card.from_strs("10", "D") in dealer_hand
    assert len(dealer_hand) == 6


def test_go_alone():
    g = initial_game_state()
    next_state = g.perform_move('call', 1, True)
    assert next_state.sitting == 3


def test_skip_discard_on_alone():
    g = initial_game_state()
    g.perform_move('pass_bid', 1)
    next_state = g.perform_move('call', 2, True)
    assert isinstance(next_state, PlayCardsPhase)


def test_proceed_to_bid_phase_two():
    g = initial_game_state()
    g.perform_move('pass_bid', 1)
    g.perform_move('pass_bid', 2)
    g.perform_move('pass_bid', 3)
    next_state = g.perform_move('pass_bid', 0)
    assert isinstance(next_state, BidPhaseTwo)


def test_call_bid_two():
    g = initial_game_state()
    g.perform_move('pass_bid', 1)
    g.perform_move('pass_bid', 2)
    g.perform_move('pass_bid', 3)
    g.perform_move('pass_bid', 0)
    next_state = g.perform_move('call', 1, False, Suit.spades)
    assert isinstance(next_state, PlayCardsPhase)
    assert next_state.trump == Suit.spades


def test_turned_down_trump():
    g = initial_game_state()
    g.perform_move('pass_bid', 1)
    g.perform_move('pass_bid', 2)
    g.perform_move('pass_bid', 3)
    g.perform_move('pass_bid', 0)
    with pytest.raises(IllegalMoveException):
        g.perform_move('call', 1, False, Suit.diamonds)


def test_stick_dealer():
    g = initial_game_state()
    g.perform_move('pass_bid', 1)
    g.perform_move('pass_bid', 2)
    g.perform_move('pass_bid', 3)
    g.perform_move('pass_bid', 0)
    g.perform_move('pass_bid', 1)
    g.perform_move('pass_bid', 2)
    g.perform_move('pass_bid', 3)
    with pytest.raises(IllegalMoveException):
        g.perform_move('pass_bid', 0)


def test_discard():
    g = initial_game_state()
    initial_hand = g.state.hands[0].copy()
    g.perform_move('call', 1, False)
    next_state = g.perform_move('discard', 0, Card.from_strs("10", "D"))
    assert isinstance(next_state, PlayCardsPhase)
    assert len(next_state.hands[0]) == 5
    assert next_state.hands[0] == initial_hand


def test_invalid_discard():
    g = initial_game_state()
    g.perform_move('call', 1, False)
    with pytest.raises(IllegalMoveException):
        g.perform_move('discard', 0, Card.from_strs("10", "S"))
