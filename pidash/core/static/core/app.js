// Small helpers: a clock, and a banner when the Pi stops answering.
(() => {
  const offline = document.getElementById("offline");
  const clock = document.querySelector("[data-tz-clock]");

  const tick = () => {
    if (clock) {
      clock.textContent = new Date().toLocaleString([], {
        day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
      });
    }
  };
  tick();
  setInterval(tick, 30000);

  // HTMX polls the status partials; a failed poll means the Pi (or the app) is down.
  const setOffline = (down) => offline && offline.classList.toggle("d-none", !down);
  document.body.addEventListener("htmx:sendError", () => setOffline(true));
  document.body.addEventListener("htmx:responseError", (event) => {
    if (event.detail.xhr.status >= 500) setOffline(true);
  });
  document.body.addEventListener("htmx:afterOnLoad", () => setOffline(false));

  // A select or checkbox marked data-autosubmit applies as soon as it changes.
  document.body.addEventListener("change", (event) => {
    const field = event.target.closest("[data-autosubmit]");
    if (field && field.form) field.form.submit();
  });

  // Anything with data-confirm asks first, then shows the button as busy.
  document.body.addEventListener("submit", (event) => {
    const form = event.target;
    const question = form.dataset.confirm;
    if (question && !window.confirm(question)) {
      event.preventDefault();
      return;
    }
    const button = form.querySelector("button[data-busy]");
    if (button) {
      button.disabled = true;
      button.innerHTML =
        '<span class="spinner-border spinner-border-sm"></span> ' + (button.dataset.busyLabel || "Working");
    }
  });

  // A button can submit another form (the prompt reset), keeping its own confirmation.
  document.body.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-submits]");
    if (!trigger) return;
    event.preventDefault();
    const form = document.getElementById(trigger.dataset.submits);
    if (form) form.requestSubmit();
  });
})();
