# For test-driving purposes

from euchre.objects import *

t = Table()
ps = [Player() for _ in range(4)]
for i, p in enumerate(ps):
    p.joinTable(t, i)
t.run()
