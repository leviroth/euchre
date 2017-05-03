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

function resolvePlayerPosition(position, player) {
  switch (position) {
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

function ChatDisplay(props) {
  return (
    <div>
      {props.messages.map((message) =>
        <div key={message.when}>
          <em>{message.sender}:</em> {message.text}
        </div>
      )}
    </div>
  );
}

class ChatInput extends Component {
  constructor(props) {
    super(props);
    this.state = {value: ''};
  }

  handleChange(event) {
    this.setState({value: event.target.value});
  }

  handleKeyPress(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      if (this.handleMessage(this.state.value)) {
        this.setState({value: ''});
      }
      event.preventDefault();
    }
  }

  handleMessage(message) {
    if (message.startsWith('/')) {
      const [command, ...params] = message.split(' ');
      switch (command) {
        case "/create":
        case "/createlobby":
          this.props.createLobby(params[0]);
          return true;
        case "/join":
          this.props.joinLobby(params[0]);
          return true;
        case "/name":
        case "/setname":
          this.props.setName(params[0]);
          return true;
        case "/say":
          this.props.sendMessage(params.join(' '));
          return true;
        case "/seat":
          this.props.joinSeat(params[0]);
          return true;
        default:
          this.props.error("Unrecognized command. To start a message with '/', use '/say [message]'.")
          return false;
      }
    } else {
      this.props.sendMessage(message);
      return true;
    }
  }

  render() {
    return (
      <textarea style={{width: "100%", position: 'absolute', bottom: '200px'}}
        value={this.state.value} onChange={(e) => this.handleChange(e)}
        onKeyDown={(e) => this.handleKeyPress(e)}
      />
    );
  }
}

class ChatBox extends Component {
  render() {
    return (
      <div className="chatbox" >
        <ChatDisplay messages={this.props.messages} />
        <ChatInput
          createLobby={(name) => this.props.createLobby(name)}
          joinLobby={(lobby) => this.props.joinLobby(lobby)}
          joinSeat={(pos) => this.props.joinSeat(pos)}
          sendMessage={(msg) => this.props.sendMessage(msg)}
          setName={(name) => this.props.setName(name)}
          error={console.log}
        />
      </div>
    )
  }
}

function UIButton(props) {
  return (
    <div className="button" onClick={() => props.onClick()}>{props.children}</div>
  );
}

function LobbyTools(props) {
  return (
    <div>
      <UIButton onClick={() => props.createLobby("cool lobby")}>Create lobby</UIButton>
      <UIButton onClick={() => props.joinLobby(0)}>Join lobby</UIButton>
    </div>
  );
}

class Card extends Component {
  render() {
    return (
      <div
        className={`card card${this.props.color}`}
        onClick={() => this.props.onClick()}
      >
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
          {[...Array(n)].map((x, i) =>
            <Card
              key={i}
              color="black"
              onClick={() => false} />
           )
          }
        </div>
      </div>
    );
  }
}


function AloneControl(props) {
  return (
    <div className={props.className}>
      <span className="control-label">Go alone?</span>
      <UIButton onClick={() => props.onClick(true)}>Yes</UIButton>
      <UIButton onClick={() => props.onClick(false)}>No</UIButton>
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
          <div className={this.props.className}>
            <UIButton onClick={() => this.setState({stage: "ALONE"})}>Pick it up</UIButton>
            <UIButton onClick={() => this.props.pass()}>Pass</UIButton>
          </div>
        );
      case "ALONE":
        return <AloneControl className={this.props.className} onClick={(alone) => this.props.call(alone)}/>;
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
          <div className={this.props.className} >
            <UIButton onClick={() => this.setState({stage: "TRUMP"})}>Name trump</UIButton>
            <UIButton onClick={() => this.props.pass()}>Pass</UIButton>
          </div>
        );
      case "TRUMP":
        return (
          <div className={this.props.className}>
            <span className="control-label">Trump:</span>
            {
              "CDHS".split('').map((c) =>
                <UIButton onClick={() => this.setState({stage: "ALONE", trump: c})}>{suitToSymbol(c)}</UIButton>
              )
            }
          </div>
        );
      case "ALONE":
        return <AloneControl className={this.props.className} onClick={(alone) => this.props.call(this.state.trump, alone)}/>;
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

  static fromStr(s, onClick) {
    const [rank, suit] = s.split('.');
    return (
      <FaceUpCard suit={suit} rank={rank} key={rank + suit} onClick={onClick} />
    );
  }
}

class Hand extends Component {
  render() {
    const cardStrs = this.props.cards
    return (
      <div className="hand myhand">
        <div className="cards">
          {cardStrs.map((cardStr, index) => {
            return (
              FaceUpCard.fromStr(cardStr, () => this.props.onClick(index))
            );
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
      <div className="trick" >
        {cards.map((card, position) =>
          (card &&
           <div key={card} className={`trick${resolvePlayerPosition(position, player)} trickcard`}>
            {FaceUpCard.fromStr(card, () => false)}
           </div>
          ))}
      </div>
    );
  }
}

function Scoreboard(props) {
  const yourTeam = props.team;
  const otherTeam = 1 - yourTeam;
  return (
    <div className="scoreboard" style={{textAlign: "left"}}>
      {(props.dealing) ? <div>You are the dealer</div> : null}
      {(props.turn) ? <div>It's your turn</div> : null}
      {(props.trump !== undefined) ? <div>Trump: {props.trump}</div> : null}
      <div>Tricks taken: {props.tricks[yourTeam]}–{props.tricks[otherTeam]} </div>
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
              call={(alone) => this.props.bid1(true, alone)}
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
        {(player !== null) ?
         [0, 1, 2, 3].filter((x) => x !== player).map((position) =>
           <FaceDownHand
             size={this.props.hands[position]}
             player={resolvePlayerPosition(position, player)}
             playerName={this.props.playerNames[position]}
             key={position}
           />
         ) :
         [0, 1, 2, 3].map((position) =>
           <UIButton onClick={() => this.props.joinSeat(position)}
             key={position}>Join seat</UIButton>)
        }
        {this.props.phase && this.props.phase.startsWith("bid") &&
         <div className="upcard">
           {FaceUpCard.fromStr(this.props.upcard, () => false)}
         </div>}
        <Hand
          playerName={this.props.playerNames[this.props.player]}
          cards={this.props.hand}
          onClick={(i) => this.props.handleCardClick(i)}
        />
        {this.renderBidControls()}
        {phase === "play" && <Trick cards={this.props.trick} />}
      </div>
    );
  }
}

class Lobby extends Component {
  addMessage(message) {
    message.when = Date.now();
    this.setState((prevState) => ({messages: prevState.messages.concat(message)}));
  }

  bid1(call, alone) {
    const session = this.props.session;
    if (call) {
      session.call(`player${this.props.player}.perform_move`, [this.props.number, 'call_one', alone]);
    } else {
      session.call(`player${this.props.player}.perform_move`, [this.props.number, 'pass_bid']);
    }
  }

  bid2(call, alone, suit) {
    const session = this.props.session;
    if (call) {
      session.call(`player${this.props.player}.perform_move`, [this.props.number, 'call_two', alone, suit]);
    } else {
      session.call(`player${this.props.player}.perform_move`, [this.props.number, 'pass_bid']);
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
    this.props.session.call(`player${this.props.player}.perform_move`, [this.props.number, phase, card]);
  }

  myTurn() {
    return this.props.gameState.turn === this.props.position;
  }

  sendMessage(message) {
    const messageObj = {text: message, sender: this.props.name};
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
          handleCardClick={(i) => this.handleCardClick(i)}
          joinSeat={(pos) => this.props.joinSeat(pos)}
        />
        <div className="grid_4 sidebar" >
          <ChatBox
            sendMessage={(msg) => this.sendMessage(msg)}
            joinSeat={(pos) => this.joinSeat(pos)}
            setName={(name) => this.setName(name)}
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
    this.state = {
      activeLobby: null,
      lobbies: Object(),
      name: ""
    };
  }

  joinServer(playerName) {
    const p = this.session.call('join_server', [playerName]);
    p.then((res) => {
      console.log(`Player ID: ${res}`);
      this.player = res;
      this.setState({name: 'anon'});
    }).catch(console.log);
    return p;
  }

  setName(name) {
    this.session.call(`player${this.player}.set_name`, [name]);
  }

  trackGame(lobbyId) {
    this.session.subscribe(`lobby${lobbyId}.publicstate`, ([res]) =>
      this.setState((prevState) =>
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
                }}}}})));
    this.session.subscribe(`lobby${lobbyId}.hands.player${this.player}`, ([res]) =>
      this.setState((prevState) =>
        update(prevState, {
          lobbies: {
            [lobbyId]: {
              gameState: {
                $merge: {
                  hand: res
                }}}}})
      ));
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

    this.setState((prevState) =>
      update(prevState, {
        lobbies: {
          [lobby]: {$set: lobbyState}}
      })
    );
    this.session.subscribe(`lobby${lobby}.chat`, (res) => this.addMessage(res[0]));
    this.trackGame(lobby);
    if (this.state.activeLobby === null) {
      this.setState({activeLobby: lobby});
    }
    console.log("subscribed");
  }

  joinLobby(lobby) {
    this.session.call(`player${this.player}.join_lobby`, [lobby])
        .then((res) =>
          this.addLobbyState(lobby));
  }

  createLobby(name) {
    this.session.call(`player${this.player}.create_lobby`, [name]).then((res) =>
      this.addLobbyState(res));
  }

  joinSeat(lobby, position) {
    this.session.call(`player${this.player}.join_seat`, [lobby, position])
        .then(() =>
          this.setState((prevState) =>
            update(prevState, {
              lobbies: {
                [lobby]: {
                  position: {
                    $set: position
                  }
                }
              }
            })));
  }

  componentDidMount() {
    /* const wsuri = "ws://localhost:8080/ws";*/
    const wsuri = `ws://${document.location.hostname}:8080/ws`

    // the WAMP connection to the Router
    this.connection = new autobahn.Connection({
      url: wsuri,
      realm: "realm1"
    });

    // fired when connection is established and session attached
    this.connection.onopen = (session, details) => {
      this.session = session;
      this.joinServer("Anonymous").then((res) => {this.player = res[0]; console.log(this.player)});
      console.log("Connected");
    };

    // fired when connection was lost (or could not be established)
    //
    this.connection.onclose = function(reason, details) {
      console.log("Connection lost: " + reason);
    }

    // now actually open the connection
    this.connection.open();
  }

  render() {
    const activeLobby = this.state.activeLobby;
    if (activeLobby !== null) {
      const lobbyState = this.state.lobbies[activeLobby];
      return (
        <Lobby gameState={lobbyState.gameState}
        player={this.player}
        number={activeLobby}
        messages={lobbyState.messages}
        seats={lobbyState.seats}
        position={lobbyState.position}
        session={this.session}
        joinSeat={(pos) => this.joinSeat(activeLobby, pos)}
        />
      );
    } else {
      return <LobbyTools
               createLobby={(name) => this.createLobby(name)}
               joinLobby={(lobby) => this.joinLobby(lobby)}
             />;
    }
  }
}

export default App;
