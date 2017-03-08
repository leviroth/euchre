from operator import itemgetter

from .exceptions import IllegalMoveException, OutOfTurnException
from .objects import Deck, Rank


def deal():
    """Return pair containing tuple of new hands and upcard."""
    deck = Deck()
    deck.shuffle()
    hands = []
    for i in range(4):
        hands.append([deck.draw() for _ in range(5)])
    return (hands, deck.draw())


class Game:
    """Context for game state."""
    moves = "call pass_bid discard play".split()

    def __init__(self, state):
        self.state = state

    def perform_move(self, move, player, *args, **kwargs):
        """Perform move, provided it is player's turn. Rerturn resulting state.

        Caller is responsible for ensuring that arguments are of correct type.

        """
        if move not in self.moves:
            raise RuntimeError("No such move")
        if player != self.state.turn:
            raise OutOfTurnException(player, self.state.turn)
        try:
            self.state = self.state.__getattribute__(move)(*args, **kwargs)
            return self.state
        except AttributeError:
            raise IllegalMoveException("Wrong phase for that move")


class Phase:
    """Base class for all game phases.

    Concrete subclasses implement a state machine.
    """
    pass


class GameOver(Phase):
    def __init__(self, winning_team):
        self.winning_team = winning_team


class LiveGamePhase:
    """Base class for all phases until game ends."""
    def __init__(self, score, hands, dealer, turn):
        self.score = score
        self.hands = hands
        self.dealer = dealer
        self.turn = turn

    @property
    def across(self):
        """The partner of the player whose turn it is."""
        return (self.turn + 2) % 4

    def card_in_hand(self, card):
        return card in self.current_hand

    @property
    def current_hand(self):
        """The hand of the player whose turn it is."""
        return self.hands[self.turn]

    @property
    def left(self):
        """The player to the left of the player whose turn it is."""
        return self.left_of(self.turn)

    def left_of(self, player, spots=1):
        """Advance the given number of spots from the given player."""
        return (player + spots) % 4


class BidPhase(LiveGamePhase):
    """Base class for bidding phases."""
    def __init__(self, score, hands, dealer, turn, up_card):
        super().__init__(score, hands, dealer, turn)
        self.up_card = up_card


class BidPhaseOne(BidPhase):
    """First bid phase, before the upcard is turned down."""
    def __str__(self):
        return "bid1"

    def call(self, alone):
        """Order the dealer to pick up the upcard."""
        self.hands[self.dealer].append(self.up_card)
        if alone:
            if self.across == self.dealer:
                return PlayCardsPhase(self.score, self.hands, self.dealer,
                                      self.left, self.across,
                                      self.up_card.suit, Trick(self.dealer),
                                      [0, 0])
            else:
                return DiscardPhase(self.score, self.hands, self.dealer,
                                    self.turn, self.across, self.up_card.suit)
        else:
            return DiscardPhase(self.score, self.hands, self.dealer, self.turn,
                                None, self.up_card.suit)

    def pass_bid(self):
        """Pass the bid to the next player."""
        if self.turn == self.dealer:
            return BidPhaseTwo(self.score, self.hands, self.dealer, self.left,
                               self.up_card)
        else:
            return BidPhaseOne(self.score, self.hands, self.dealer, self.left,
                               self.up_card)


class BidPhaseTwo(BidPhase):
    def __str__(self):
        return "bid2"

    def call(self, alone, trump):
        """Name trump."""
        if trump == self.up_card.suit:
            raise IllegalMoveException()
        if alone:
            return PlayCardsPhase(self.score, self.hands, self.dealer,
                                  self.left, self.across, self.turn, trump,
                                  Trick(self.left), [0, 0])
        else:
            next_turn = self.left_of(self.dealer)
            return PlayCardsPhase(self.score, self.hands, self.dealer,
                                  next_turn, self.turn, None,
                                  trump, Trick(next_turn), [0, 0])

    def pass_bid(self):
        """Pass the bid to the next player."""
        if self.turn == self.dealer:
            raise IllegalMoveException()
        else:
            return BidPhaseTwo(self.score, self.hands, self.dealer, self.left,
                               self.up_card)


class TrumpMadePhase(LiveGamePhase):
    """Base class for phases that have a trump suit made."""
    def __init__(self, score, hands, dealer, turn, maker, sitting, trump):
        super().__init__(score, hands, dealer, turn)
        self.maker = maker
        self.sitting = sitting
        self.trump = trump


class DiscardPhase(TrumpMadePhase):
    """Short phase where the dealer discards a card."""
    def __init__(self, score, hands, dealer, maker, sitting, trump):
        super().__init__(score, hands, dealer, dealer, maker, sitting, trump)

    def discard(self, card):
        """Discard a card."""
        if not self.card_in_hand(card):
            raise IllegalMoveException()

        self.hands[self.dealer].remove(card)
        if self.sitting is None:
            next_player = self.left
        else:
            next_player = self.left_of(self.maker)
        return PlayCardsPhase(self.score, self.hands, self.dealer, next_player,
                              self.sitting, self.trump, self.trump,
                              Trick(next_player), [0, 0])


class PlayCardsPhase(TrumpMadePhase):
    """The main phase of play."""
    def __init__(self, score, hands, dealer, turn, maker, sitting, trump,
                 trick, trick_score):
        super().__init__(score, hands, dealer, turn, maker, sitting, trump)
        self.trick = trick
        self.trick_score = trick_score

    def cannot_follow(self):
        """Return true if the player has no card in the led suit."""
        return not any(self.following_suit(card) for card in self.current_hand)

    def check_legal_move(self, card):
        """Check that the player has card and follows suit if possible."""
        if not self.card_in_hand(card):
            raise IllegalMoveException()
        if not self.following_suit(card) and not self.cannot_follow():
            raise IllegalMoveException()

    def following_suit(self, card):
        """Return true if card follows suit, given current trump.

        The first card of the trick always counts as following suit.
        """
        if len(self.trick) == 0:
            return True
        return self.relative_suit(card) == self.led_suit()

    def led_suit(self):
        return self.relative_suit(self.trick.led())

    @property
    def relative_left(self):
        """Return the player to the left, accounting for going-alone."""
        if self.sitting == self.left:
            return self.left_of(self.turn, 2)
        return self.left

    def next_hand_or_victory(self):
        """Proceed to next hand, or end game if someone has won."""
        for team, score in enumerate(self.score):
            if score >= 10:
                return GameOver(team)

        new_hands, new_up_card = deal()

        return BidPhaseOne(self.score, new_hands, self.left_of(self.dealer),
                           self.left_of(self.dealer, spots=1), new_up_card)

    def play(self, card):
        """Play a card."""
        self.check_legal_move(card)
        self.current_hand.remove(card)
        self.trick.add_card(self.turn, card)
        if self.trick_full():
            return self.score_trick()
        self.turn = self.relative_left
        return self

    def relative_rank(self, card):
        """Turn a card into an ordered pair for scoring.

        The built-in ordering of the return values corresponds to the ordering
        of the cards in scoring a trick.

        relative_rank(None) compares less than any card; this helps us handle
        the sitting player.

        """
        if self.relative_suit(card) == self.trump:
            suit_score = 2
        elif self.relative_suit(card) == self.led_suit():
            suit_score = 1
        else:
            suit_score = 0

        if suit_score == 2 and card.rank == Rank.jack:
            if card.suit == self.trump:
                rank_score = 21
            else:
                rank_score = 20
        else:
            rank_score = int(card.rank)

        return (suit_score, rank_score)

    def relative_suit(self, card):
        """Return the suit of a card, accounting for trump."""
        if card.rank == Rank.jack and card.color == self.trump.color:
            return self.trump
        return card.suit

    def trick_full(self):
        """Check if all cards have been played for this trick."""
        max_size = 3 if self.sitting is not None else 4
        return max_size == len(self.trick)

    def trick_winner(self):
        """Find the winner of the current trick."""
        return max(range(4),
                   key=lambda x: self.relative_rank(self.trick.cards.get(x)))

    def score_trick(self):
        """Return next state after trick is finished."""
        winning_player = self.trick_winner()
        winning_team = winning_player % 2
        self.trick_score[winning_team] += 1
        if sum(self.trick_score) == 5:
            return self.score_round()
        self.turn = winning_player
        self.trick = Trick(winning_player)
        return self

    def score_round(self):
        """Update game score after round and advance state."""
        winning_team, tricks_taken = max(enumerate(self.trick_score),
                                         key=itemgetter(1))
        if winning_team != self.maker % 2:
            points = 2
        else:
            if tricks_taken == 5:
                points = 4 if self.sitting is not None else 2
            else:
                points = 1
        self.score[winning_team] += points
        return self.next_hand_or_victory()


class Trick:
    """A simple representation of a trick."""
    def __init__(self, leader):
        self.leader = leader
        self.cards = {}

    def __len__(self):
        return len(self.cards)

    def add_card(self, player, card):
        self.cards[player] = card

    def led(self):
        """The card that was led."""
        return self.cards[self.leader]
