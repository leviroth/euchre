from test_game import (initial_game_state, play_phase_start_state,
                       round_almost_won_state)
from euchre.encoder import to_serializable

expected_initial_game_state = {
    'score': [0, 0],
    'hands':
    [['A.S', 'K.S', 'J.S', 'Q.H', '9.D'], ['A.C', 'K.C', 'J.C', 'Q.D', '9.H'],
     ['A.H', 'K.H', 'J.H', 'Q.C', '9.C'], ['A.D', 'K.D', 'J.D', 'Q.S', '9.S']],
    'dealer':
    0,
    'turn':
    1,
    'up_card':
    '10.D',
    'phase':
    'bid1'
}

expected_play_phase_start_state = {
    'score': [0, 0],
    'hands':
    [['A.S', 'K.S', 'J.S', 'Q.H', '9.D'], ['A.C', 'K.C', 'J.C', 'Q.D', '9.H'],
     ['A.H', 'K.H', 'J.H', 'Q.C', '9.C'], ['A.D', 'K.D', 'J.D', 'Q.S', '9.S']],
    'dealer':
    0,
    'turn':
    1,
    'maker':
    1,
    'sitting':
    None,
    'trump':
    'S',
    'trick': {},
    'trick_score': [0, 0],
    'phase':
    'play'
}
expected_round_almost_won_state = {
    'score': [0, 0],
    'hands': [['A.C'], ['A.D'], ['A.H'], ['A.S']],
    'dealer': 0,
    'turn': 1,
    'maker': 1,
    'sitting': None,
    'trump': 'S',
    'trick': {},
    'trick_score': [2, 2],
    'phase': 'play'
}


def test_state_encoding():
    expecteds = [
        expected_initial_game_state, expected_play_phase_start_state,
        expected_round_almost_won_state
    ]
    for state, expected in zip(
        [initial_game_state, play_phase_start_state,
         round_almost_won_state], expecteds):
        assert to_serializable(state().state) == expected
