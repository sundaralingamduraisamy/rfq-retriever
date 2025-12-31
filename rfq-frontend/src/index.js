import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// ---- FIX ResizeObserver UI Crash ----
const resizeObserverErrMsg =
  "ResizeObserver loop completed with undelivered notifications.";

window.addEventListener("error", (e) => {
  if (e.message === resizeObserverErrMsg) {
    e.stopImmediatePropagation();
  }
});

window.addEventListener("unhandledrejection", (e) => {
  if (
    e?.reason?.message &&
    e.reason.message.includes("ResizeObserver loop")
  ) {
    e.preventDefault();
  }
});
// -------------------------------------

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  // If still glitching, REMOVE StrictMode. React double renders components.
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
