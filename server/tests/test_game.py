"""Test the Game class for correct implementation of game logic."""
import pytest

from euchre.exceptions import IllegalMoveException, OutOfTurnException
from euchre.game import (BidPhaseOne, BidPhaseTwo, DiscardPhase, Game,
                         GameOver, PlayCardsPhase, Trick)
from euchre.objects import Card, Suit


def hand_from_str(s):
    """Return a list of Card objects from a list of space-separated strings."""
    return [Card.from_str(card_str) for card_str in s.split()]


def initial_game_state():
    hand_strs = ["A.S K.S J.S Q.H 9.D",
                 "A.C K.C J.C Q.D 9.H",
                 "A.H K.H J.H Q.C 9.C",
                 "A.D K.D J.D Q.S 9.S"]
    score = [0, 0]
    hands = [hand_from_str(s) for s in hand_strs]
    up_card = Card.from_str("10.D")
    initial_phase = BidPhaseOne(score, hands, 0, 1, up_card)
    return Game(initial_phase)


def play_phase_start_state(trump=Suit.spades):
    hand_strs = ["A.S K.S J.S Q.H 9.D",
                 "A.C K.C J.C Q.D 9.H",
                 "A.H K.H J.H Q.C 9.C",
                 "A.D K.D J.D Q.S 9.S"]
    score = [0, 0]
    hands = [hand_from_str(s) for s in hand_strs]
    dealer = 0
    turn = 1
    maker = 1
    sitting = None
    trick = Trick(turn)
    trick_score = [0, 0]
    phase = PlayCardsPhase(score, hands, dealer, turn, maker, sitting, trump,
                           trick, trick_score)
    return Game(phase)


def round_almost_won_state(trump=Suit.spades):
    hand_strs = ["A.C",
                 "A.D",
                 "A.H",
                 "A.S"]
    score = [0, 0]
    hands = [hand_from_str(s) for s in hand_strs]
    dealer = 0
    turn = 1
    maker = 1
    sitting = None
    trick = Trick(turn)
    trick_score = [2, 2]
    phase = PlayCardsPhase(score, hands, dealer, turn, maker, sitting, trump,
                           trick, trick_score)
    return Game(phase)


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
        g.perform_move('discard', 1, Card.from_str("Q.D"))


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
    assert Card.from_str("10.D") in dealer_hand
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
    next_state = g.perform_move('discard', 0, Card.from_str("10.D"))
    assert isinstance(next_state, PlayCardsPhase)
    assert len(next_state.hands[0]) == 5
    assert next_state.hands[0] == initial_hand


def test_invalid_discard():
    g = initial_game_state()
    g.perform_move('call', 1, False)
    with pytest.raises(IllegalMoveException):
        g.perform_move('discard', 0, Card.from_str("10.S"))


def test_play_card():
    g = play_phase_start_state()
    next_state = g.perform_move('play', 1, Card.from_str("A.C"))
    assert next_state.trick.cards == {1: Card.from_str("A.C")}
    next_state = g.perform_move('play', 2, Card.from_str("9.C"))
    assert next_state.trick.cards == {1: Card.from_str("A.C"),
                                      2: Card.from_str("9.C")}


def test_play_full_trick():
    g = play_phase_start_state()
    g.perform_move('play', 1, Card.from_str("A.C"))
    g.perform_move('play', 2, Card.from_str("9.C"))
    g.perform_move('play', 3, Card.from_str("9.S"))
    next_state = g.perform_move('play', 0, Card.from_str("J.S"))
    assert next_state.trick.leader == 0
    assert next_state.trick_score == [1, 0]
    assert all(len(hand) == 4 for hand in next_state.hands)


def test_check_reneg():
    g = play_phase_start_state()
    g.perform_move('play', 1, Card.from_str("A.C"))
    with pytest.raises(IllegalMoveException):
        g.perform_move('play', 2, Card.from_str("A.H"))


def test_check_reneg__forced():
    g = play_phase_start_state()
    g.state.hands[2][4] = Card.from_str("A.H")
    g.perform_move('play', 1, Card.from_str("A.C"))
    with pytest.raises(IllegalMoveException):
        g.perform_move('play', 2, Card.from_str("A.H"))


def test_check_reneg__jack():
    """Check that left bower is counted as trump suit."""
    g = play_phase_start_state(trump=Suit.clubs)
    g.state.hands[2] = hand_from_str("10.C J.S A.C Q.C K.C")
    g.perform_move('play', 1, Card.from_str("A.C"))
    g.perform_move('play', 2, Card.from_str("J.S"))


def test_win_round__make():
    g = round_almost_won_state()
    g.perform_move('play', 1, Card.from_str("A.D"))
    g.perform_move('play', 2, Card.from_str("A.H"))
    g.perform_move('play', 3, Card.from_str("A.S"))
    next_state = g.perform_move('play', 0, Card.from_str("A.C"))
    assert next_state.score == [0, 1]


def test_win_round__march():
    g = round_almost_won_state()
    g.state.trick_score = [0, 4]
    g.perform_move('play', 1, Card.from_str("A.D"))
    g.perform_move('play', 2, Card.from_str("A.H"))
    g.perform_move('play', 3, Card.from_str("A.S"))
    next_state = g.perform_move('play', 0, Card.from_str("A.C"))
    assert next_state.score == [0, 2]


def test_win_round__euchre():
    g = round_almost_won_state()
    g.state.maker = 2
    g.perform_move('play', 1, Card.from_str("A.D"))
    g.perform_move('play', 2, Card.from_str("A.H"))
    g.perform_move('play', 3, Card.from_str("A.S"))
    next_state = g.perform_move('play', 0, Card.from_str("A.C"))
    assert next_state.score == [0, 2]


def test_win_round__alone():
    g = round_almost_won_state()
    g.state.trick_score = [0, 4]
    g.state.sitting = 3
    g.perform_move('play', 1, Card.from_str("A.D"))
    g.perform_move('play', 2, Card.from_str("A.H"))
    next_state = g.perform_move('play', 0, Card.from_str("A.C"))
    assert next_state.score == [0, 4]


def test_win_game():
    g = round_almost_won_state()
    g.state.score = [9, 9]
    g.perform_move('play', 1, Card.from_str("A.D"))
    g.perform_move('play', 2, Card.from_str("A.H"))
    g.perform_move('play', 3, Card.from_str("A.S"))
    next_state = g.perform_move('play', 0, Card.from_str("A.C"))
    assert isinstance(next_state, GameOver)
    assert next_state.winning_team == 1
