from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import json
import euchre.objects


class Communicator:
    @staticmethod
    def phasemap(phase, turn):
        phasecode = {euchre.phases.Bid1Phase: "bid1",
                     euchre.phases.Bid2Phase: "bid2",
                     euchre.phases.PlayPhase: "play",
                     euchre.phases.DiscardPhase: "disc"}[phase]

        turncode = turn.n

        return {"phase": phasecode, "turn": turncode}


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")
        self.player = euchre.objects.Player()

    def onMessage(self, payload, isBinary):
        msg = json.loads(payload.decode('utf8'))
        if msg['command'] == "connect":
            self.player.setName("John")
            self.player.joinTable(self.factory.table, 1)
            self.factory.register(self)
            print(self.player)
            self.ps = [euchre.objects.Player() for _ in range(3)]
            for i, p in zip([0, 2, 3], self.ps):
                p.joinTable(self.factory.table, i)
            self.factory.table.run()

        if msg['command'] == 'bid1':
            try:
                data = msg['data']
                self.player.bid1(data['bid'], data['alone'])
            except euchre.exceptions.TurnError:
                print("ok, turn error")
            else:
                self.factory.broadcast(
                    Communicator.phasemap(
                        self.factory.table.hand.phase.__class__,
                        self.factory.table.hand.phase.turn
                    ))
                self.factory.broadcast(
                    {"command": "message",
                     "data": "{} pased".format(str(self.player))
                     }
                )

        if msg['command'] == 'bid2':
            try:
                data = msg['data']
                self.player.bid2(data['bid'], data['alone'], data['suit'])
            except euchre.exceptions.TurnError:
                print("ok, turn error")
            else:
                self.factory.broadcast(
                    Communicator.phasemap(
                        self.factory.table.hand.phase.__class__,
                        self.factory.table.hand.phase.turn
                    ))
                self.factory.broadcast(
                    {"command": "message",
                     "data": "{} pased".format(str(self.player))
                     }
                )

        if msg['command'] == 'play':
            try:
                cdata = msg['data']['card']
                c = euchre.objects.Card.fromStrs(cdata['rank'], cdata['suit'])
                self.player.playCard(c)
            except euchre.exceptions.TurnError:
                print("ok, turn error")
            else:
                self.factory.broadcast(
                    Communicator.phasemap(
                        self.factory.table.hand.phase.__class__,
                        self.factory.table.hand.phase.turn
                    ))
                self.factory.broadcast(
                    {"command": "message",
                     "data": "{} pased".format(str(self.player))
                     }
                )

        if msg['command'] == 'discard':
            try:
                cdata = msg['data']['card']
                c = euchre.objects.Card.fromStrs(cdata['rank'], cdata['suit'])
                self.player.discard(c)
            except euchre.exceptions.TurnError:
                print("ok, turn error")
            else:
                self.factory.broadcast(
                    Communicator.phasemap(
                        self.factory.table.hand.phase.__class__,
                        self.factory.table.hand.phase.turn
                    ))
                self.factory.broadcast(
                    {"command": "message",
                     "data": "{} pased".format(str(self.player))
                     }
                )

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


class EuchreFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = euchre.objects.Table()
        self.players = []

    def register(self, player):
        self.players.append(player)

    def broadcast(self, payload):
        for player in self.players:
            message = json.dumps(payload, ensure_ascii=False).encode('utf8')
            player.sendMessage(message, isBinary=False)


if __name__ == '__main__':

    try:
        import asyncio
    except ImportError:
        # Trollius >= 0.3 was renamed
        import trollius as asyncio

    factory = EuchreFactory(u"ws://127.0.0.1:9000")
    factory.protocol = MyServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 9000)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
