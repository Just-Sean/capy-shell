// capy-shell responsive nav drawer (feature 4).
//
// The drawer opens and closes on its own with a checkbox + CSS (see shell.css).
// This script is progressive enhancement that adds the accessibility behavior:
// it keeps the burger's aria-expanded in sync, moves focus into the drawer when it
// opens and back to the burger when it closes, closes it on Escape, and keeps Tab
// inside it while it's open on small screens. With JavaScript off the drawer still
// opens and closes from the burger and the backdrop — just without focus handling.

(function () {
  "use strict";

  var toggle = document.getElementById("capy-shell-drawer-toggle");
  var button = document.getElementById("capy-shell-drawer-button");
  var drawer = document.getElementById("capy-shell-nav");
  if (!toggle || !button || !drawer) {
    return; // No sidebar on this page: nothing to enhance.
  }

  // A fallback focus target when the drawer has no focusable items yet.
  if (!drawer.hasAttribute("tabindex")) {
    drawer.setAttribute("tabindex", "-1");
  }

  var mobile = window.matchMedia("(max-width: 767.98px)");

  function focusables() {
    // The native focusable elements, in document order. `summary` matters here: a
    // nav built from <details><summary> is a real tab stop, and leaving it out
    // would mis-compute the first/last stop and let the trap leak.
    var selector =
      'a[href], button:not([disabled]), input:not([disabled]), ' +
      'select:not([disabled]), textarea:not([disabled]), summary, ' +
      'iframe, audio[controls], video[controls], [contenteditable], ' +
      '[tabindex]:not([tabindex="-1"])';
    return Array.prototype.filter.call(
      drawer.querySelectorAll(selector),
      function (el) {
        return el.offsetParent !== null; // Only what's actually visible.
      }
    );
  }

  function isOpen() {
    return toggle.checked;
  }

  function sync() {
    button.setAttribute("aria-expanded", isOpen() ? "true" : "false");
    button.setAttribute(
      "aria-label",
      isOpen() ? "Close navigation menu" : "Open navigation menu"
    );
  }

  // The burger and the backdrop are <label>s, so a mouse toggles the checkbox and
  // `change` fires for both. Keep aria in sync and move focus to match the state.
  toggle.addEventListener("change", function () {
    sync();
    if (isOpen()) {
      var items = focusables();
      (items[0] || drawer).focus();
    } else {
      button.focus();
    }
  });

  // Labels aren't keyboard-activatable, so drive the toggle from the burger for
  // Enter and Space (its role="button" promises that). click() flips the checkbox
  // and fires the change handler above.
  button.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " " || event.key === "Spacebar") {
      event.preventDefault();
      toggle.click();
    }
  });

  // Escape closes the drawer from anywhere while it's open.
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && isOpen()) {
      toggle.click();
    }
  });

  // Keep Tab inside the drawer while it's open on a small screen.
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Tab" || !isOpen() || !mobile.matches) {
      return;
    }
    var items = focusables();
    if (items.length === 0) {
      event.preventDefault();
      drawer.focus();
      return;
    }
    var first = items[0];
    var last = items[items.length - 1];
    var active = document.activeElement;
    if (event.shiftKey && (active === first || active === drawer)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  });

  // Growing to `md` and up docks the drawer; drop the open state so it and its
  // backdrop don't linger. Setting .checked directly doesn't fire change, so sync.
  mobile.addEventListener("change", function (event) {
    if (!event.matches && isOpen()) {
      toggle.checked = false;
      sync();
    }
  });

  sync();
})();
