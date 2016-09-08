from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import json
import euchre.objects


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
            print(self.player)
            self.ps = [euchre.objects.Player() for _ in range(3)]
            for i, p in zip([0, 2, 3], self.ps):
                p.joinTable(self.factory.table, i)
            self.factory.table.run()

        if msg['command'] == 'call':
            try:
                self.player.bid1(True, False)
            except euchre.exceptions.TurnError:
                print("ok, turn error")

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


class EuchreFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = euchre.objects.Table()


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
