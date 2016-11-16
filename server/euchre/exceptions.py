class TurnError(Exception):
    def __init__(self, expression, turn=None):
        self.expression = expression
        self.turn = turn
