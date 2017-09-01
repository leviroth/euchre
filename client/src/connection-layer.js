class GameAPIConnection {
  constructor(session, playerID) {
    this.session = session;
    this.playerID = playerID;
  }

  callAPI(endpoint, args) {
    return this.session.call(endpoint, args);
  }

  callPlayerAPI(endpoint, args) {
    return this.callAPI(`player${this.playerID}.${endpoint}`, args);
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

  getPlayers() {
    return this.callAPI("players");
  }

  getSeats() {
    return this.callAPI("seats");
  }

  joinSeat(position) {
    return this.callPlayerAPI("join_seat", [position]);
  }

  performMove(...args) {
    this.callPlayerAPI("perform_move", args);
  }

  sendMessage(message) {
    this.session.publish(
      "chat",
      [{ senderID: this.playerID, body: message }],
      {},
      { exclude_me: false }
    );
  }

  setName(name) {
    this.callPlayerAPI("set_name", [name]);
  }

  startGame() {
    this.callPlayerAPI("start_game");
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

  subscribeToPlayers(callback) {
    this.subscribe("players", callback);
  }

  subscribeToPublicState(callback) {
    this.subscribe("publicstate", ([res]) => callback(this.translateStateDict(res)));
  }

  subscribeToSeats(callback) {
    this.subscribe("seats", callback);
  }

  translateStateDict(state) {
    return {
      dealer: state.dealer,
      hands: state.hands,
      phase: state.phase,
      score: state.score,
      sitting: state.sitting,
      trick: state.trick,
      trickScore: state.trick_score,
      trump: state.trump,
      turn: state.turn,
      upcard: state.up_card
    };
  }
}

export default GameAPIConnection;
