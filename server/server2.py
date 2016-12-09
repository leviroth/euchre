import euchre.objects
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import functools


class MyComponent(ApplicationSession):
    async def onJoin(self, details):
        print("session joined")
        print("Details: {}".format(details))

        self.players = dict()
        self.player_count = 0
        self.hand = None

        def deal():
            for player_id, player in self.players.items():
                self.publish('realm1.p{}.hand'.format(player_id),
                             [str(card) for card in player.hand])
            self.publish('realm1.newhand')

        def new_trick():
            self.publish('realm1.newtrick')

        ui = euchre.objects.UserInterface(
            new_hand=deal,
            new_trick=new_trick,
            card_played=lambda x: self.publish('realm1.card_played', x)
            )

        self.t = euchre.objects.Table(lambda x: self.publish('realm1.msg', x),
                                      ui)

        def create_player(name="Player"):
            player = euchre.objects.Player()
            player.setName(name)
            self.players[self.player_count] = player
            self.player_count += 1
            return self.player_count - 1

        async def run():
            print("running")
            for player_id, player in self.players.items():
                await self.register(
                    functools.partial(bid1, player),
                    'realm1.p{}.bid1'.format(player_id))
                await self.register(
                    functools.partial(bid2, player),
                    'realm1.p{}.bid2'.format(player_id))
                await self.register(
                    functools.partial(discard, player),
                    'realm1.p{}.discard'.format(player_id))
                await self.register(
                    functools.partial(play_card, player),
                    'realm1.p{}.play'.format(player_id))
            self.t.run()
            deal()
            publish_state()

        def join_table(player, position):
            self.players[player].joinTable(self.t, position)
            print("player {} joined".format(player))

        def publish_state():
            loner = None
            try:
                if self.t.hand.phase.alone:
                    loner = self.t.hand.phase.maker
            except AttributeError:
                pass

            tricks_taken = [0, 0]
            try:
                tricks_taken = list(self.t.hand.phase.tricksTaken.values())
            except AttributeError:
                pass

            self.publish('realm1.state', {
                "upcard": str(self.t.hand.upCard),
                "phase": str(self.t.hand.phase),
                "turn": self.t.hand.phase.turn.position,
                "dealer": self.t.hand.dealer.position,
                "score": self.t.points,
                "alone": loner,
                "trickScore": tricks_taken
            })

        def bid1(player, call, alone):
            try:
                player.bid1(call, alone)
                publish_state()
                dealer = self.t.hand.dealer
                self.publish('realm1.p{}.hand'.format(dealer.position),
                             [str(card) for card in dealer.hand])
                return True
            except Exception as e:
                return False

        def bid2(player, call, alone, suit):
            try:
                player.bid2(call, alone, suit)
                publish_state()
                return True
            except Exception as e:
                return False

        def discard(player, card_str):
            card = euchre.objects.Card.fromStrs(*card_str.split('.'))
            try:
                player.discard(card)
                publish_state()
                return True
            except Exception:
                return False

        def play_card(player, card_str):
            card = euchre.objects.Card.fromStrs(*card_str.split('.'))
            try:
                player.playCard(card)
            except Exception as e:
                print(e)
                return False
            else:
                publish_state()
                return True

        await self.register(create_player, 'realm1.create_player')
        await self.register(join_table, 'realm1.join_table')
        await self.register(run, 'realm1.run')


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://localhost:8080/ws", realm=u"realm1")
    runner.run(MyComponent)
