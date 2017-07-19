from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from bidict import bidict
from .game import Game, initial_game_state
from .encoder import to_serializable
from .objects import Card


class GameLayer:
    def __init__(self, game):
        self.game = game

    @property
    def state(self):
        return self.game.state

    def perform_move(self, move, player, *args):
        if move == 'call_two':
            alone = args[0]
            suit = Card.suit_map[args[1]]
            return self.game.perform_move(move, player, alone, suit)
        if move == 'discard' or move == 'play':
            card = Card.from_str(args[0])
            return self.game.perform_move(move, player, card)
        return self.game.perform_move(move, player, *args)


class Lobby:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.game = None
        self.seats_to_players = bidict()

    def change_seat(self, player, seat):
        self.join_seat(player, seat)
        self.leave_seat(player)

    def check_seat_open(self, seat):
        if seat < 0 or seat > 3:
            raise RuntimeError("No such seat.")
        if seat in self.seats_to_players:
            raise RuntimeError("Seat is taken.")

    def join_seat(self, player, seat):
        self.check_seat_open(seat)
        self.seats_to_players[seat] = player

    def leave_seat(self, player):
        if self.game is not None:
            raise RuntimeError("Not in the middle of a game!")
        del self.seats_to_players.inv[player]

    def perform_move(self, move, player, *args, **kwargs):
        self.game.perform_move(move, self.seats_to_players.inv[player],
                               *args, **kwargs)
        self.coordinator.publish_state()

    def start_game(self):
        if len(self.seats_to_players) != 4:
            raise RuntimeError("Not enough players.")
        self.game = GameLayer(Game(initial_game_state()))
        self.coordinator.publish_state()


class Player:
    def __hash__(self):
        return self.player_id

    def __init__(self, player_id, name, coordinator):
        self.player_id = player_id
        self.name = name
        self.coordinator = coordinator

    def change_seat(self, lobby_id, seat):
        self.coordinator.lobby.change_seat(self, seat)

    def join_seat(self, seat):
        self.coordinator.lobby.join_seat(self, seat)

    def perform_move(self, move, *args, **kwargs):
        self.coordinator.lobby.perform_move(move, self, *args, **kwargs)

    def start_game(self):
        self.coordinator.lobby.start_game()


class Coordinator(ApplicationSession):
    def publish_state(self):
        serializable_state = to_serializable(self.lobby.game.state)
        if 'hands' in serializable_state:
            serializable_state['hands'] = [
                len(hand) for hand in serializable_state['hands']
            ]
        self.publish('publicstate', serializable_state)
        for seat, player in self.lobby.seats_to_players.items():
            self.publish(
                'hands.player{pn}'.format(pn=player.player_id),
                to_serializable(self.lobby.game.state.hands[seat]))

    async def onJoin(self, details):
        print("session joined")
        print("Details: {}".format(details))

        self.players = dict()
        self.player_count = 0
        self.lobby = Lobby(self)

        async def join_server(name=None):
            player_id = self.player_count
            if name is None:
                name = "Player {}".format(player_id)
            self.player_count += 1
            player = Player(player_id, name, self)
            self.players[player_id] = player

            await self.register(
                player.perform_move,
                'player{n}.perform_move'.format(n=player_id))
            await self.register(
                player.start_game,
                'player{n}.start_game'.format(n=player_id))
            await self.register(
                player.join_seat,
                'player{n}.join_seat'.format(n=player_id))
            await self.register(
                player.change_seat,
                'player{n}.change_seat'.format(n=player_id))

            return player_id, name

        await self.register(join_server, 'join_server')


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://localhost:8080/ws", realm=u"realm1")
    runner.run(Coordinator)
