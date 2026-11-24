// Give immediate feedback while the browser waits for the synchronous
// /simulate request. The server still renders the authoritative final state.
(function () {
  "use strict";

  function whenReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  whenReady(function () {
    var form = document.querySelector('form[action="/simulate"]');
    var status = document.getElementById("sim-run-state");
    if (!form || !status) return;

    var label = status.querySelector(".run-status__label");
    var detail = status.querySelector(".run-status__detail");
    var button = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", function () {
      status.dataset.state = "RUNNING";
      status.setAttribute("aria-current", "step");
      status.setAttribute("aria-busy", "true");
      if (label) label.textContent = "RUNNING";
      if (detail) detail.textContent = "กำลังรัน ngspice — กรุณารอผลลัพธ์";
      if (button) {
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
      }
    });

    // Restore controls when the user returns through the browser history cache.
    window.addEventListener("pageshow", function (event) {
      if (!event.persisted) return;
      if (button) {
        button.disabled = false;
        button.removeAttribute("aria-busy");
      }
      status.removeAttribute("aria-current");
      status.setAttribute("aria-busy", "false");
    });
  });
})();
