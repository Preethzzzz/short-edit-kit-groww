// Shared by every shot: wait for fonts and pictures, then show each [data-from] element from that second on.
export function shot(duration) {
  const pics = [...document.images].map(i => i.decode().catch(() => {}));
  window.film = {
    duration,
    ready: Promise.all([document.fonts.load('800 60px "Inter Tight"'), document.fonts.load('500 26px "Inter Tight"'), ...pics]).then(() => document.fonts.ready),
    frame(t) {
      for (const el of document.querySelectorAll("[data-from]")) el.style.display = t >= +el.dataset.from ? "block" : "none";
    },
  };
}
