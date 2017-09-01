Version 0.2.0 of this repository constitutes a rough, but fully playable
web-based, multiplayer [Euchre](https://en.wikipedia.org/wiki/Euchre) game. To
get it up and running, you'll need to make sure that you have
[Crossbar.io](http://crossbar.io/) and Node. The various components are started
with:

    $ cd router/
    $ crossbar start
    
    $ cd server/
    $ python server.py
    
    $ cd client/
    $ npm start
    
### Limitations and TODOs ###

- [ ] There are no credentials involved in the protocol. While the game does not
  deliberately broadcast the contents of other players' hands, you can obtain
  this information if you abuse the API. Similarly, you can issue commands on
  behalf of other players.
  
- [ ] The game is ugly, and some UI elements overlap each other.

- [ ] The UI makes use of CSS Grid features that aren't available on Internet
  Explorer.
