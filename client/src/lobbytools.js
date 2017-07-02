import React, { Component } from "react";
import UIButton from "./uibutton.js";

class LobbyTools extends Component {
  constructor() {
    super();
    this.state = { lobbies: [] };
  }

  componentDidMount() {
    this.props.session.call("get_lobbies", []).then(res => this.setState({ lobbies: res }));
  }

  lobbyList() {
    return (
      <div className="lobbyList">
        {Object.entries(this.state.lobbies).map(([key, value]) => (
          <UIButton onClick={() => this.props.joinLobby(Number(key))} key={key}>{value}</UIButton>
        ))}
      </div>
    );
  }

  render() {
    return (
      <div>
        <UIButton onClick={() => this.props.createLobby("cool lobby")}>
          Create lobby
        </UIButton>
        {this.lobbyList()}
      </div>
    );
  }
}

export default LobbyTools;
