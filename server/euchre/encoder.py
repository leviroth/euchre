from functools import singledispatch

from .game import (BidPhaseOne, BidPhaseTwo, DiscardPhase, PlayCardsPhase,
                   Phase, GameOver, Trick)
from .objects import Card, Suit


PHASE_NAMES = {
    BidPhaseOne: 'bid1',
    BidPhaseTwo: 'bid2',
    DiscardPhase: 'discard',
    PlayCardsPhase: 'play',
    GameOver: 'gameover',
}


@singledispatch
def to_serializable(val):
    return val


@to_serializable.register(dict)
def _(val):
    return {to_serializable(k): to_serializable(v) for k, v in val.items()}


@to_serializable.register(list)  # noqa: F811
@to_serializable.register(tuple)
def _(val):
    return [to_serializable(x) for x in val]


@to_serializable.register(Phase)  # noqa: F811
def _(val):
    d = to_serializable(vars(val))
    d['phase'] = PHASE_NAMES[type(val)]
    return d


@to_serializable.register(Suit)  # noqa: F811
def _(val):
    return str(val)


@to_serializable.register(Trick)  # noqa: F811
def _(val):
    return to_serializable(val.cards)


@to_serializable.register(Card)  # noqa: F811
def _(val):
    return str(val)
