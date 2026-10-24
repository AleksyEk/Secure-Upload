"use strict";

const notification = document.querySelector(".notification");

if (notification) {
  let remaining = Number(notification.dataset.timeout);
  let startedAt;
  let timer;
  let animationFrame;
  let dismissed = false;
  const duration = remaining;
  const progress = notification.querySelector(".countdown-progress");

  function paintCountdown() {
    if (dismissed || timer === undefined) return;
    const left = Math.max(0, remaining - (performance.now() - startedAt));
    progress.setAttribute("stroke-dashoffset", String(100 * (1 - left / duration)));
    animationFrame = window.requestAnimationFrame(paintCountdown);
  }

  function dismiss() {
    if (dismissed) return;
    dismissed = true;
    window.clearTimeout(timer);
    window.cancelAnimationFrame(animationFrame);
    progress.setAttribute("stroke-dashoffset", "100");
    // Po zamknięciu klawiaturą przenieś fokus do dostępnego elementu strony.
    if (notification.contains(document.activeElement)) {
      document.querySelector("#file").focus();
    }
    notification.classList.add("is-hiding");
    window.setTimeout(() => { notification.hidden = true; }, 200);
  }

  function resume() {
    if (dismissed || timer !== undefined || notification.matches(":hover, :focus-within")) return;
    startedAt = performance.now();
    timer = window.setTimeout(dismiss, Math.max(0, remaining));
    paintCountdown();
  }

  function pause() {
    if (timer === undefined) return;
    window.clearTimeout(timer);
    window.cancelAnimationFrame(animationFrame);
    remaining = Math.max(0, remaining - (performance.now() - startedAt));
    progress.setAttribute("stroke-dashoffset", String(100 * (1 - remaining / duration)));
    timer = undefined;
  }

  notification.querySelector(".notification-close").addEventListener("click", dismiss);
  notification.addEventListener("mouseenter", pause);
  notification.addEventListener("mouseleave", resume);
  notification.addEventListener("focusin", pause);
  notification.addEventListener("focusout", () => window.setTimeout(resume, 0));
  notification.addEventListener("keydown", (event) => {
    if (event.key === "Escape") dismiss();
  });
  resume();

  // Odświeżenie strony po sukcesie nie powinno ponownie wyświetlać komunikatu.
  const url = new URL(window.location.href);
  if (url.searchParams.has("uploaded") || url.searchParams.has("deleted")) {
    url.searchParams.delete("uploaded");
    url.searchParams.delete("deleted");
    window.history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
}
