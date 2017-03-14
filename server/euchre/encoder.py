import json
from .game import (
    BidPhaseOne, BidPhaseTwo, DiscardPhase, PlayCardsPhase, GameOver, Trick)
from .objects import Card, Suit


class CardEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Card):
            return str(o)
        return super().default(o)


class PublicStateEncoder(CardEncoder):
    DICT_ENCODE = {BidPhaseOne: 'bid1',
                   BidPhaseTwo: 'bid2',
                   DiscardPhase: 'discard',
                   PlayCardsPhase: 'play',
                   GameOver: 'gameover',
                   }

    def default(self, o):
        for t in self.DICT_ENCODE:
            if isinstance(o, t):
                d = {k: v for k, v in o.__dict__.items() if k != 'hands'}
                d['hands'] = [len(hand) for hand in o.hands]
                d['phase'] = self.DICT_ENCODE[t]
                return d
        if isinstance(o, Suit):
            return str(o)
        if isinstance(o, Trick):
            return o.cards
        return super().default(o)
