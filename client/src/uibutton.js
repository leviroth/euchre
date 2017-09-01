import React from "react";

function UIButton(props) {
  let classes = "button";
  if (props.className !== undefined) {
    classes += " " + props.className;
  }
  return (
    <div className={classes} onClick={() => props.onClick()}>
      {props.children}
    </div>
  );
}

export default UIButton;
