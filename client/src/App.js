import React, { Component } from "react";
import update from "immutability-helper";
import autobahn from "autobahn";

import "./App.css";
import ChatBox from "./chat.js";
import { suitToSymbol } from "./helpers.js";
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

class GameAPIConnection {
  constructor(session, playerID) {
    this.session = session;
    this.playerID = playerID;
  }

  callAPI(endpoint, args) {
    return this.session.call(`player${this.playerID}.${endpoint}`, args);
  }

  bid1(call, alone) {
    if (call) {
      this.performMove("call_one", alone);
    } else {
      this.performMove("pass_bid");
    }
  }

  bid2(call, alone, suit) {
    if (call) {
      this.performMove("call_two", alone, suit);
    } else {
      this.performMove("pass_bid");
    }
  }

  joinSeat(position) {
    return this.callAPI("join_seat", [position]);
  }

  performMove(...args) {
    this.callAPI("perform_move", args);
  }

  sendMessage(message) {
    this.callAPI("chat", [message]);
    /* this.addMessage(messageObj);*/
  }

  setName(name) {
    this.callAPI("set_name", [name]);
  }

  subscribe(endpoint, callback) {
    this.session.subscribe(endpoint, callback);
  }

  subscribeToHand(callback) {
    this.subscribe(`hands.player${this.playerID}`, callback);
  }

  subscribeToChat(callback) {
    this.subscribe("chat", callback);
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
              call={alone => this.props.gameAPIConnection.bid1(true, alone)}
              pass={() => this.props.gameAPIConnection.bid1(false, false)}
            />
          );
        case "bid2":
          return (
            <Bid2Controls
              className="bid-controls"
              call={(trump, alone) => this.props.gameAPIConnection.bid2(true, trump, alone)}
              pass={() => this.props.gameAPIConnection.bid2(false, false, null)}
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

  handleCardClick(i) {
    if (!this.myTurn()) {
      return;
    }
    const phase = this.props.gameState.phase;
    if (phase !== "play" && phase !== "discard") {
      return;
    }

    const card = this.props.gameState.hand[i];
    this.props.gameAPIConnection.performMove(phase, card);
  }

  myTurn() {
    return this.props.gameState.turn === this.props.position;
  }

  render() {
    const gameState = this.props.gameState;
    const team = this.props.position % 2;
    return (
      <div className="container_12 App">
        <Table
          gameAPIConnection={this.props.gameAPIConnection}
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
    this.state = { gameAPIConnection: null };
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
      session
        .call("join_server", [])
        .then(([playerID]) => {
          this.setState({ gameAPIConnection: new GameAPIConnection(session, playerID) });
          console.log("Player ID: " + playerID);
        })
        .catch(console.log);
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
    return this.state.gameAPIConnection
      ? <ConnectedApp gameAPIConnection={this.state.gameAPIConnection} />
      : <div>Connecting...</div>;
  }
}

class ConnectedApp extends Component {
  constructor() {
    super();
    const baseGameState = {
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
    };

    this.state = {
      gameState: baseGameState,
      messages: [],
      seats: Array(4).fill(null),
      position: null
    };
  }

  trackGame() {
    this.props.gameAPIConnection.subscribe(`publicstate`, ([res]) =>
      this.setState(prevState =>
        update(prevState, {
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
        })
      )
    );
    this.props.gameAPIConnection.subscribeToHand(([res]) =>
      this.setState(prevState =>
        update(prevState, {
          gameState: {
            $merge: {
              hand: res
            }
          }
        })
      )
    );
  }

  componentDidMount() {
    this.props.gameAPIConnection.subscribeToChat(res => this.addMessage(res[0]));
    this.trackGame();
    console.log("subscribed");
  }

  joinSeat(position) {
    this.props.gameAPIConnection.joinSeat(position).then(() =>
      // TODO: could the following be simplified to setState({position})?
      this.setState(prevState =>
        update(prevState, {
          position: {
            $set: position
          }
        })
      )
    );
  }

  render() {
    return (
      <Lobby
        gameState={this.state.gameState}
        player={this.player}
        seats={this.state.seats}
        position={this.state.position}
        messages={this.state.messages}
        gameAPIConnection={this.props.gameAPIConnection}
        joinSeat={pos => this.joinSeat(pos)}
      />
    );
  }
}

export default App;
