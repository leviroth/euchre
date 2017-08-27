import React, { Component } from "react";

function ChatDisplay(props) {
  return (
    <div>
      {props.messages.map(message => (
        <div key={message.when}>
          <em>{props.players[message.senderID]}:</em> {message.body}
        </div>
      ))}
    </div>
  );
}

class ChatInput extends Component {
  constructor(props) {
    super(props);
    this.state = { value: "" };
  }

  handleChange(event) {
    this.setState({ value: event.target.value });
  }

  handleKeyPress(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      if (this.handleMessage(this.state.value)) {
        this.setState({ value: "" });
      }
      event.preventDefault();
    }
  }

  handleMessage(message) {
    if (message.startsWith("/")) {
      const [command, ...params] = message.split(" ");
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
          this.props.sendMessage(params.join(" "));
          return true;
        case "/seat":
          this.props.joinSeat(params[0]);
          return true;
        default:
          this.props.error(
            "Unrecognized command. To start a message with '/', use '/say [message]'."
          );
          return false;
      }
    } else {
      this.props.sendMessage(message);
      return true;
    }
  }

  render() {
    return (
      <textarea
        style={{ width: "100%", position: "absolute", bottom: "200px" }}
        value={this.state.value}
        onChange={e => this.handleChange(e)}
        onKeyDown={e => this.handleKeyPress(e)}
      />
    );
  }
}

class ChatBox extends Component {
  render() {
    const connection = this.props.gameAPIConnection;
    return (
      <div className="chatbox">
        <ChatDisplay players={this.props.players} messages={this.props.messages} />
        <ChatInput
          createLobby={name => connection.createLobby(name)}
          joinSeat={pos => connection.joinSeat(pos)}
          sendMessage={msg => connection.sendMessage(msg)}
          setName={name => connection.setName(name)}
          error={console.log}
        />
      </div>
    );
  }
}

export default ChatBox;
