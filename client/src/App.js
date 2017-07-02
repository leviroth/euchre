import React, { Component } from "react";
import update from "immutability-helper";
import autobahn from "autobahn";

import "./App.css";
import ChatBox from "./chat.js";
import { suitToSymbol } from "./helpers.js";
import LobbyTools from "./lobbytools.js";
import { Bid1Controls, Bid2Controls } from "./movecontrols.js";
import UIButton from "./uibutton.js";

function resolvePlayerPosition(position, player) {
  switch (Number(position)) {
    case (player + 1) % 4:
      return "left";
    case (player + 2) % 4:
      return "top";
    case (player + 3) % 4:
      return "right";
    default:
      return "bottom";
  }
}

class Card extends Component {
  render() {
    return (
      <div className={`card card${this.props.color}`} onClick={() => this.props.onClick()}>
        {this.props.children}
      </div>
    );
  }
}

class FaceDownHand extends Component {
  render() {
    const n = this.props.size;
    return (
      <div className={`hand ${this.props.player}hand`}>
        <div className="playername">{this.props.playerName}</div>
        <div className="cards">
          {[...Array(n)].map((x, i) => <Card key={i} color="black" onClick={() => false} />)}
        </div>
      </div>
    );
  }
}

class FaceUpCard extends Component {
  constructor(props) {
    super(props);
    if (this.props.suit === "D" || this.props.suit === "H") {
      this.color = "red";
    } else {
      this.color = "black";
    }

    this.suitSymbol = suitToSymbol(this.props.suit);
  }

  render() {
    return (
      <Card color={this.color} onClick={() => this.props.onClick()}>
        {this.props.rank + this.suitSymbol}
      </Card>
    );
  }

  static fromStr(s, onClick) {
    const [rank, suit] = s.split(".");
    return <FaceUpCard suit={suit} rank={rank} key={rank + suit} onClick={onClick} />;
  }
}

class Hand extends Component {
  render() {
    const cardStrs = this.props.cards;
    return (
      <div className="hand myhand">
        <div className="cards">
          {cardStrs.map((cardStr, index) => {
            return FaceUpCard.fromStr(cardStr, () => this.props.onClick(index));
          })}
        </div>
        <div className="playername">{this.props.playerName}</div>
      </div>
    );
  }
}

class Trick extends Component {
  render() {
    const cards = this.props.cards;
    const player = this.props.player;
    return (
      <div className="trick">
        {Object.entries(cards).map(
          ([position, card]) =>
            card &&
            <div key={card} className={`trick${resolvePlayerPosition(position, player)} trickcard`}>
              {FaceUpCard.fromStr(card, () => false)}
            </div>
        )}
      </div>
    );
  }
}

function Scoreboard(props) {
  const yourTeam = props.team;
  const otherTeam = 1 - yourTeam;
  return (
    <div className="scoreboard" style={{ textAlign: "left" }}>
      {props.dealing ? <div>You are the dealer</div> : null}
      {props.turn ? <div>It's your turn</div> : null}
      {props.trump !== undefined ? <div>Trump: {props.trump}</div> : null}
      <div>
        Tricks taken: {props.tricks[yourTeam]}–{props.tricks[otherTeam]}{" "}
      </div>
      <div>Score: {props.scores[yourTeam]}–{props.scores[otherTeam]}</div>
    </div>
  );
}

class Table extends Component {
  myTurn() {
    return this.props.turn === this.props.player;
  }

  renderBidControls() {
    if (this.myTurn()) {
      switch (this.props.phase) {
        case "bid1":
          return (
            <Bid1Controls
              className="bid-controls"
              call={alone => this.props.bid1(true, alone)}
              pass={() => this.props.bid1(false, false)}
            />
          );
        case "bid2":
          return (
            <Bid2Controls
              className="bid-controls"
              call={(trump, alone) => this.props.bid2(true, trump, alone)}
              pass={() => this.props.bid2(false, false, null)}
            />
          );
        default:
          return null;
      }
    }
  }

  render() {
    const phase = this.props.phase;
    const player = this.props.position;

    return (
      <div className="grid_8" id="table">
        {player !== null
          ? [0, 1, 2, 3]
              .filter(x => x !== player)
              .map(position => (
                <FaceDownHand
                  size={this.props.hands[position]}
                  player={resolvePlayerPosition(position, player)}
                  playerName={this.props.playerNames[position]}
                  key={position}
                />
              ))
          : [0, 1, 2, 3].map(position => (
              <UIButton onClick={() => this.props.joinSeat(position)} key={position}>
                Join seat
              </UIButton>
            ))}
        {this.props.phase &&
          this.props.phase.startsWith("bid") &&
          <div className="upcard">
            {FaceUpCard.fromStr(this.props.upcard, () => false)}
          </div>}
        <Hand
          playerName={this.props.playerNames[this.props.player]}
          cards={this.props.hand}
          onClick={i => this.props.handleCardClick(i)}
        />
        {this.renderBidControls()}
        {phase === "play" && <Trick cards={this.props.trick} player={player} />}
      </div>
    );
  }
}

class Lobby extends Component {
  addMessage(message) {
    message.when = Date.now();
    this.setState(prevState => ({
      messages: prevState.messages.concat(message)
    }));
  }

  bid1(call, alone) {
    const session = this.props.session;
    if (call) {
      session.call(`player${this.props.player}.perform_move`, [
        this.props.number,
        "call_one",
        alone
      ]);
    } else {
      session.call(`player${this.props.player}.perform_move`, [this.props.number, "pass_bid"]);
    }
  }

  bid2(call, alone, suit) {
    const session = this.props.session;
    if (call) {
      session.call(`player${this.props.player}.perform_move`, [
        this.props.number,
        "call_two",
        alone,
        suit
      ]);
    } else {
      session.call(`player${this.props.player}.perform_move`, [this.props.number, "pass_bid"]);
    }
  }

  handleCardClick(i) {
    if (!this.myTurn()) {
      return;
    }
    const phase = this.props.gameState.phase;
    if (phase !== "play" && phase !== "discard") {
      return;
    }

    const card = this.props.gameState.hand[i];
    this.props.session.call(`player${this.props.player}.perform_move`, [
      this.props.number,
      phase,
      card
    ]);
  }

  myTurn() {
    return this.props.gameState.turn === this.props.position;
  }

  sendMessage(message) {
    const messageObj = { text: message, sender: this.props.name };
    this.props.session.publish(`lobby${this.props.num}.chat`, [messageObj]);
    this.addMessage(messageObj);
  }

  render() {
    const gameState = this.props.gameState;
    const team = this.props.position % 2;
    return (
      <div className="container_12 App">
        <Table
          hand={gameState.hand}
          hands={gameState.hands}
          upcard={gameState.upcard}
          phase={gameState.phase}
          turn={gameState.turn}
          dealer={gameState.dealer}
          alone={gameState.alone}
          trick={gameState.trick}
          trickScore={gameState.trickScore}
          score={gameState.score}
          player={this.props.position}
          playerNames={this.props.seats}
          bid1={(...args) => this.bid1(...args)}
          bid2={(...args) => this.bid2(...args)}
          position={this.props.position}
          handleCardClick={i => this.handleCardClick(i)}
          joinSeat={pos => this.props.joinSeat(pos)}
        />
        <div className="grid_4 sidebar">
          <ChatBox
            sendMessage={msg => this.sendMessage(msg)}
            joinSeat={pos => this.joinSeat(pos)}
            setName={name => this.setName(name)}
            messages={this.props.messages}
          />
          <Scoreboard
            dealing={gameState.dealer === this.props.position}
            scores={gameState.score}
            team={team}
            tricks={gameState.trickScore}
            trump={gameState.trump}
            turn={this.myTurn()}
          />
        </div>
      </div>
    );
  }
}

class App extends Component {
  constructor() {
    super();
    this.state = { session: null };
  }

  componentDidMount() {
    const wsuri = `ws://${document.location.hostname}:8080/ws`;

    // the WAMP connection to the Router
    this.connection = new autobahn.Connection({
      url: wsuri,
      realm: "realm1"
    });

    // fired when connection is established and session attached
    this.connection.onopen = (session, details) => {
      this.setState({ session: session });
      console.log("Connected");
    };

    // fired when connection was lost (or could not be established)
    //
    this.connection.onclose = function(reason, details) {
      console.log("Connection lost: " + reason);
    };

    // now actually open the connection
    this.connection.open();
  }

  render() {
    return this.state.session
      ? <ConnectedApp session={this.state.session} />
      : <div>Connecting...</div>;
  }
}

class ConnectedApp extends Component {
  constructor() {
    super();
    this.state = {
      activeLobby: null,
      lobbies: Object(),
      name: ""
    };
  }

  componentDidMount() {
    this.joinServer("Anonymous").then(res => {
      this.player = res[0];
      console.log(this.player);
    });
  }

  joinServer(playerName) {
    const p = this.props.session.call("join_server", [playerName]);
    p
      .then(res => {
        console.log(`Player ID: ${res}`);
        this.player = res;
        this.setState({ name: "anon" });
      })
      .catch(console.log);
    return p;
  }

  setName(name) {
    this.props.session.call(`player${this.player}.set_name`, [name]);
  }

  trackGame(lobbyId) {
    this.props.session.subscribe(`lobby${lobbyId}.publicstate`, ([res]) =>
      this.setState(prevState =>
        update(prevState, {
          lobbies: {
            [lobbyId]: {
              gameState: {
                $merge: {
                  dealer: res.dealer,
                  hands: res.hands,
                  phase: res.phase,
                  score: res.score,
                  sitting: res.sitting,
                  trick: res.trick,
                  trickScore: res.trick_score,
                  trump: res.trump,
                  turn: res.turn,
                  upcard: res.up_card
                }
              }
            }
          }
        })
      )
    );
    this.props.session.subscribe(`lobby${lobbyId}.hands.player${this.player}`, ([res]) =>
      this.setState(prevState =>
        update(prevState, {
          lobbies: {
            [lobbyId]: {
              gameState: {
                $merge: {
                  hand: res
                }
              }
            }
          }
        })
      )
    );
  }

  addLobbyState(lobby) {
    const lobbyState = {
      gameState: {
        dealer: null,
        hand: [],
        hands: Array(4).fill(0),
        phase: null,
        score: [0, 0],
        sitting: null,
        trickScore: [0, 0],
        tricks: [],
        turn: null,
        upcard: null
      },
      messages: [],
      seats: Array(4).fill(null),
      position: null
    };

    this.setState(prevState =>
      update(prevState, {
        lobbies: {
          [lobby]: { $set: lobbyState }
        }
      })
    );
    this.props.session.subscribe(`lobby${lobby}.chat`, res => this.addMessage(res[0]));
    this.trackGame(lobby);
    if (this.state.activeLobby === null) {
      this.setState({ activeLobby: lobby });
    }
    console.log("subscribed");
  }

  joinLobby(lobby) {
    this.props.session
      .call(`player${this.player}.join_lobby`, [lobby])
      .then(res => this.addLobbyState(lobby));
  }

  createLobby(name) {
    this.props.session
      .call(`player${this.player}.create_lobby`, [name])
      .then(res => this.addLobbyState(res));
  }

  joinSeat(lobby, position) {
    this.props.session.call(`player${this.player}.join_seat`, [lobby, position]).then(() =>
      this.setState(prevState =>
        update(prevState, {
          lobbies: {
            [lobby]: {
              position: {
                $set: position
              }
            }
          }
        })
      )
    );
  }

  render() {
    const activeLobby = this.state.activeLobby;
    if (activeLobby !== null) {
      const lobbyState = this.state.lobbies[activeLobby];
      return (
        <Lobby
          gameState={lobbyState.gameState}
          player={this.player}
          number={activeLobby}
          messages={lobbyState.messages}
          seats={lobbyState.seats}
          position={lobbyState.position}
          session={this.props.session}
          joinSeat={pos => this.joinSeat(activeLobby, pos)}
        />
      );
    } else {
      return (
        <LobbyTools
          createLobby={name => this.createLobby(name)}
          joinLobby={lobby => this.joinLobby(lobby)}
          session={this.props.session}
        />
      );
    }
  }
}

export default App;
