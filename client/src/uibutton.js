import React from "react";

function UIButton(props) {
  return (
    <div className="button" onClick={() => props.onClick()}>
      {props.children}
    </div>
  );
}

export default UIButton;
