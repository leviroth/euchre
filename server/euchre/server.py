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
            for player in self.players.values():
                self.publish('realm1.p{}.hand'.format(player.position),
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

        def set_name(player_id, name):
            self.players[player_id].setName(name)
            self.publish('realm1.player_names', [player_id, name])

        def set_position(player_id, position):
            self.players[player_id].set_position(position)

        async def run():
            print("running")
            self.t.run()
            deal()
            publish_state()

        async def join_table(player_num, position):
            player = self.players[player_num]
            player.joinTable(self.t, position)
            await self.register(functools.partial(bid1, player),
                                'realm1.p{}.bid1'.format(player.position))
            await self.register(functools.partial(bid2, player),
                                'realm1.p{}.bid2'.format(player.position))
            await self.register(functools.partial(discard, player),
                                'realm1.p{}.discard'.format(player.position))
            await self.register(functools.partial(play_card, player),
                                'realm1.p{}.play'.format(player.position))
            print("player {} ({}) joined at position {}"
                  .format(player_num, player.name, position))

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
        await self.register(set_name, 'realm1.set_name')
        await self.register(set_position, 'realm1.set_position')
        await self.register(join_table, 'realm1.join_table')
        await self.register(run, 'realm1.run')


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://localhost:8080/ws", realm=u"realm1")
    runner.run(MyComponent)
