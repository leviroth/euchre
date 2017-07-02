import React, { Component } from "react";

import { suitToSymbol } from "./helpers.js";
import UIButton from "./uibutton.js";

function AloneControl(props) {
  return (
    <div className={props.className}>
      <span className="control-label">Go alone?</span>
      <UIButton onClick={() => props.onClick(true)}>Yes</UIButton>
      <UIButton onClick={() => props.onClick(false)}>No</UIButton>
    </div>
  );
}

export class Bid1Controls extends Component {
  constructor() {
    super();
    this.state = { stage: "CALL" };
  }

  render() {
    switch (this.state.stage) {
      case "CALL":
        return (
          <div className={this.props.className}>
            <UIButton onClick={() => this.setState({ stage: "ALONE" })}>
              Pick it up
            </UIButton>
            <UIButton onClick={() => this.props.pass()}>Pass</UIButton>
          </div>
        );
      case "ALONE":
        return (
          <AloneControl
            className={this.props.className}
            onClick={alone => this.props.call(alone)}
          />
        );
      default:
        return null;
    }
  }
}

export class Bid2Controls extends Component {
  constructor() {
    super();
    this.state = { stage: "CALL" };
  }

  render() {
    switch (this.state.stage) {
      case "CALL":
        return (
          <div className={this.props.className}>
            <UIButton onClick={() => this.setState({ stage: "TRUMP" })}>
              Name trump
            </UIButton>
            <UIButton onClick={() => this.props.pass()}>Pass</UIButton>
          </div>
        );
      case "TRUMP":
        return (
          <div className={this.props.className}>
            <span className="control-label">Trump:</span>
            {"CDHS".split("").map(c => (
              <UIButton onClick={() => this.setState({ stage: "ALONE", trump: c })}>
                {suitToSymbol(c)}
              </UIButton>
            ))}
          </div>
        );
      case "ALONE":
        return (
          <AloneControl
            className={this.props.className}
            onClick={alone => this.props.call(this.state.trump, alone)}
          />
        );
      default:
        return null;
    }
  }
}
