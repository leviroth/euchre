import React, {
  Component
} from 'react';
import update from 'immutability-helper';
import './App.css';
import autobahn from 'autobahn';

function suitToSymbol(suit) {
  switch (suit) {
    case "C":
      return "\u2663";
    case "D":
      return "\u2666";
    case "H":
      return "\u2665";
    case "S":
      return "\u2660";
    default:
      return undefined;
  }
}

class Card extends Component {
  render() {
    return (
      <div
        className={`card${this.props.color}`}
        onClick={() => this.props.onClick()}
      >
        {this.props.children}
      </div>
    );
  }
}

function AloneControl(props) {
  return (
    <div>
      Go alone?
      <button onClick={() => props.onClick(true)}>Yes</button>
      <button onClick={() => props.onClick(false)}>No</button>
    </div>
  );
}

class Bid1Controls extends Component {
  constructor() {
    super();
    this.state = {stage: "CALL"};
  }

  render() {
    switch (this.state.stage) {
      case "CALL":
        return (
          <div>
            <button onClick={() => this.setState({stage: "ALONE"})}>Pick it up</button>
            <button onClick={() => this.props.pass()}>Pass</button>
          </div>
        );
      case "ALONE":
        return <AloneControl onClick={(alone) => this.props.call(alone)}/>;
      default:
        return null;
    }
  }
}

class Bid2Controls extends Component {
  constructor() {
    super();
    this.state = {stage: "CALL"};
  }

  render() {
    switch (this.state.stage) {
      case "CALL":
        return (
          <div>
            <button onClick={() => this.setState({stage: "TRUMP"})}>Name trump</button>
            <button onClick={() => this.props.pass()}>Pass</button>
          </div>
        );
      case "TRUMP":
        return (
          <div>
            Trump:
            {
              "CDHS".split('').map((c) =>
                <button onClick={() => this.setState({stage: "ALONE", trump: c})}>{suitToSymbol(c)}</button>
              )
            }
          </div>
        );
      case "ALONE":
        return <AloneControl onClick={(alone) => this.props.call(this.state.trump, alone)}/>;
      default:
        return null;
    }
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
}

class Hand extends Component {
  cardFromStr(s) {
    const [rank, suit] = s.split('.');
    return {
      rank,
      suit
    };
  }

  render() {
    const cards = this.props.cards.map(this.cardFromStr, this);
    return (
      <div>{cards.map((card, index) => {
          return (
            <FaceUpCard
              suit={card.suit}
              rank={card.rank}
              key={card.rank + card.suit}
              onClick={() => this.props.onClick(index)} />
          );
        })}
      </div>
    );
  }
}

function Scoreboard(props) {
  return (
    <div style={{textAlign: "left"}}>
      {(props.dealing) ? <div>You are the dealer</div> : null}
      {(props.turn) ? <div>It's your turn</div> : null}
      {(props.trump !== undefined) ? <div>Trump: {props.trump}</div> : null}
      <div>Tricks taken: {props.tricks} </div>
      <div>Score: {props.yourScore}–{props.theirScore}</div>
    </div>
  );
}

class App extends Component {
  constructor() {
    super();
    this.state = {
      hand: [],
      upcard: null,
      phase: null,
      turn: null,
      dealer: null,
      alone: null,
      score: [3, 5] //FOR TESTING
    };

    const wsuri = "ws://localhost:8080/ws";

    // the WAMP connection to the Router
    this.connection = new autobahn.Connection({
      url: wsuri,
      realm: "realm1"
    });

    // fired when connection is established and session attached
    this.connection.onopen = (session, details) => {
      this.session = session;
      console.log(" Connected");

      session.call('realm1.create_player', ["Fred"])
        .then((res) => {
          console.log(`Player ID: ${res}`);
          this.player = res;
          session.call("realm1.join_table", [res, res])
            .then(console.log);
          session.subscribe(`realm1.p${this.player}.hand`,
            (res) => this.setState({"hand": res[0]}));
          session.subscribe('realm1.state',
            (res) => this.setState(res[0]));
          console.log("subscribe point");
        })
        .catch(console.log);
    };

    // fired when connection was lost (or could not be established)
    //
    this.connection.onclose = function(reason, details) {
      console.log("Connection lost: " + reason);
    }

    // now actually open the connection
    this.connection.open();
  }

  run() {
    this.session.call('realm1.run');
  }

  removeCard(index) {
    this.setState((prevState) =>
      update(prevState, {
        hand: {
          $splice: [
            [index, 1]
          ]
        }
      })
    );
  }

  handleCardClick(i) {
    if (!this.myTurn()) {
      return;
    }
    const phase = this.state.phase;
    if (phase !== "play" && phase !== "discard") {
      return;
    }

    this.session.call(`realm1.p${this.player}.${phase}`,
                        [this.state.hand[i]])
        .then((res) => {
          if (res) {
            this.removeCard(i);
          } else {
            console.log("turn error");
          }
        });
  }

  bid1(call, alone) {
    this.session.call(`realm1.p${this.player}.bid1`,
                      [call, alone]);
  }

  bid2(call, alone, suit) {
    this.session.call(`realm1.p${this.player}.bid2`,
                      [call, alone, suit]);
  }

  myTurn() {
    return this.state.turn === this.player;
  }

  renderBidControls() {
    if (this.myTurn()) {
      switch (this.state.phase) {
        case "bid1":
          return <Bid1Controls
          call={(alone) => this.bid1(true, alone)}
          pass={() => this.bid1(false, false)} />
        case "bid2":
          return <Bid2Controls
          call={(trump, alone) => this.bid2(true, trump, alone)}
          pass={() => this.bid2(false, false, null)} />
        default:
          return null;
      }
    }
  }

  handSize(player) {
    if (this.state.alone === player) {
      return 0;
    }
    const tricks = this.state.tricks;
    const playedCards = tricks.map((trick) => trick[player]).filter((x) => !!x);
    return playedCards.length;
  }
  render() {
    const topPlayer = (this.player + 2) % 4;
    const team = this.player % 2;
    return (
      <div className="App">
        <FaceDownHand size={this.handSize(topPlayer)} />
        <div>Player {this.player}</div>
        <Hand cards={this.state.hand} onClick={(i) => this.handleCardClick(i)} />
        {this.renderBidControls()}
        <button onClick={() => this.run()} >run</button>
        <Scoreboard tricks="2" yourScore={this.state.score[team]} theirScore={this.state.score[1 - team]}
          dealing={this.state.dealer === this.player}
          turn={this.myTurn()}
          trump={this.state.trump}
        />
        {(this.state.upcard !== null) ? <Hand cards={[this.state.upcard]} onClick={(i) => {}} /> : null}
      </div>
    );
  }
}

export default App;
