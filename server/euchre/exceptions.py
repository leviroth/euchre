class IllegalMoveException(Exception):
    pass


class OutOfTurnException(Exception):
    def __init__(self, attempted, actual, message="Out of turn"):
        self.attempted = attempted
        self.actual = actual
