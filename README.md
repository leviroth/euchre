Version 0.1.0 of this repository constitutes an extremely rough, but fully
playable web-based, multiplayer [Euchre](https://en.wikipedia.org/wiki/Euchre)
game. To get it up and running, you'll need to make sure that you
have [Crossbar.io](http://crossbar.io/) and Node. The various components are started with:

    $ cd router/
    $ crossbar start
    
    $ cd server/
    $ python server.py
    
    $ cd client/
    $ npm start
    
### What works ###

Provided you don't tear any of the duct tape currently holding the networking
together, you should find that you're able to play the game. You can play cards,
you will be prevented from making illegal moves, the game knows whose turn it
is, score is kept, etc.

### What doesn't ###

This software isn't alpha; it's more like Linear B.
    
The underlying networking is very fragile and makes startup a bit of a hassle
for users. Each time you load the web page, the client connects to the game as a
new user and joins the table at the first open seat. The right way to load and
play the game is to have four people load the page in order, starting with the
dealer of the first hand and proceeding in the order in which people would like
to sit around the table. Clicking "run" with greater or fewer than four players,
or while the game is already running, is going to cause a crash, at which point
you'll want to restart `server.py` and have people re-load. Clicking "debug"
will rewrite your local game state with a dummy used for testing the UI, and the
only way out is to restart the game for everyone. Reader beware.

Currently, work is underway to improve this situation. That starts with
rewriting the server to decouple the game state, and its (too "thick")
representation of a player, from the objects used to handle user interactions.
You can check out this work on the `backend-rewrite` branch.
