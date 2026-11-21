// capy-shell's own light / dark / auto toggle. capy-theme v2 exposes the theme (its
// stylesheet forces a mode with data-theme="capy-light"/"capy-dark"); the consumer
// applies the choice. This stores the visitor's choice and sets data-theme on <html>.
// "auto" follows the OS: we read prefers-color-scheme and force the matching mode (rather
// than leaving data-theme off and trusting the page's cascade), and react to OS changes,
// so auto is reliable whatever else the project's stylesheet does. Loaded non-deferred in
// <head> so the mode is applied before first paint (no flash). External file, so no inline
// script for a strict Content Security Policy.
(function () {
  "use strict";
  var root = document.documentElement;
  var COOKIE = "capy_shell_mode";
  var ORDER = ["light", "dark", "auto"];
  var YEAR = 60 * 60 * 24 * 365;
  var darkQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function stored() {
    var m = (document.cookie.match(/(?:^|; )capy_shell_mode=(light|dark|auto)/) || [])[1];
    return m || "auto";
  }

  function next(mode) {
    return ORDER[(ORDER.indexOf(mode) + 1) % ORDER.length];
  }

  function effective(mode) {
    if (mode === "auto") return darkQuery && darkQuery.matches ? "dark" : "light";
    return mode;
  }

  function apply(mode) {
    root.setAttribute("data-theme", "capy-" + effective(mode)); // force, even in auto
    root.setAttribute("data-capy-shell-mode", mode); // the chosen mode, for the icon + label
    var button = document.getElementById("capy-shell-mode");
    if (button) {
      // Name the current mode and what a click does (the icon shows the next mode).
      button.setAttribute("aria-label", "Theme: " + mode + ". Switch to " + next(mode) + ".");
    }
  }

  function set(mode) {
    document.cookie =
      COOKIE + "=" + mode + ";path=/;max-age=" + YEAR + ";samesite=lax" +
      (location.protocol === "https:" ? ";secure" : "");
    apply(mode);
    var live = document.getElementById("capy-shell-mode-live");
    if (live) live.textContent = mode + " theme"; // announced to assistive tech
  }

  apply(stored()); // before paint
  // Re-apply once the button exists, so its accessible name is right on load.
  document.addEventListener("DOMContentLoaded", function () {
    apply(stored());
  });
  // Keep auto in step with the OS while it's selected.
  if (darkQuery) {
    darkQuery.addEventListener("change", function () {
      if (stored() === "auto") apply("auto");
    });
  }
  document.addEventListener("click", function (event) {
    var hit = event.target.closest && event.target.closest("[data-capy-shell-mode-cycle]");
    if (!hit) return;
    event.preventDefault();
    set(next(stored()));
  });
})();
