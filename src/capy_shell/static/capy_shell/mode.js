// capy-shell's own light / dark / auto toggle. capy-theme v2 exposes the theme (its
// stylesheet has the light + dark values and an "auto" prefers-color-scheme rule); the
// consumer applies the choice. This stores the visitor's choice and sets data-theme on
// <html> (capy-theme's contract: data-theme="capy-light"/"capy-dark" forces a mode, none
// = auto). Loaded non-deferred in <head> so the stored mode is applied before first paint
// (no flash). External file, so no inline script for a strict Content Security Policy.
(function () {
  "use strict";
  var root = document.documentElement;
  var COOKIE = "capy_shell_mode";
  var ORDER = ["light", "dark", "auto"];
  var YEAR = 60 * 60 * 24 * 365;

  function stored() {
    var m = (document.cookie.match(/(?:^|; )capy_shell_mode=(light|dark|auto)/) || [])[1];
    return m || "auto";
  }

  function apply(mode) {
    if (mode === "auto") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", "capy-" + mode);
    root.setAttribute("data-capy-shell-mode", mode); // for the icon + label CSS
    var button = document.getElementById("capy-shell-mode");
    if (button) {
      button.setAttribute("aria-label", "Theme: " + mode + ". Activate to change.");
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
  document.addEventListener("click", function (event) {
    var hit = event.target.closest && event.target.closest("[data-capy-shell-mode-cycle]");
    if (!hit) return;
    event.preventDefault();
    set(ORDER[(ORDER.indexOf(stored()) + 1) % ORDER.length]);
  });
})();
