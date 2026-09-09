// The app's ambient, in miniature: a field of ASCII glyphs lit by two slow
// violet and blue drifts on the app's own ground. Referenced from the ASCII
// jellyfish study; rebuilt small, and still under prefers-reduced-motion.
(() => {
  const canvas = document.getElementById("ambient");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const RAMP = " .·:+*oO&8";
  const CELL = 16;
  let w, h, cols, rows;

  function size() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    w = innerWidth;
    h = innerHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cols = Math.ceil(w / CELL);
    rows = Math.ceil(h / CELL);
    ctx.font = "12px ui-monospace, Menlo, monospace";
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
  }

  function glow(x, y, cx, cy, r) {
    const fall = 1 - Math.hypot(x - cx, y - cy) / r;
    return fall > 0 ? fall * fall : 0;
  }

  function frame(t) {
    ctx.clearRect(0, 0, w, h);
    const r = Math.max(w, h) * 0.46;
    const cx1 = w * (0.5 + 0.28 * Math.sin(t * 0.00021));
    const cy1 = h * (0.4 + 0.22 * Math.cos(t * 0.00017));
    const cx2 = w * (0.5 + 0.3 * Math.cos(t * 0.00013));
    const cy2 = h * (0.6 + 0.24 * Math.sin(t * 0.00019));
    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = i * CELL + CELL / 2;
        const y = j * CELL + CELL / 2;
        const violet = glow(x, y, cx1, cy1, r);
        const blue = glow(x, y, cx2, cy2, r * 0.9);
        const v = Math.min(1, violet * 1.15 + blue);
        if (v < 0.07) continue;
        const ch = RAMP[Math.min(RAMP.length - 1, (v * RAMP.length) | 0)];
        ctx.fillStyle = violet > blue
          ? "rgba(93,35,165," + (0.05 + v * 0.15) + ")"
          : "rgba(35,75,171," + (0.05 + v * 0.13) + ")";
        ctx.fillText(ch, x, y);
      }
    }
  }

  size();
  addEventListener("resize", () => { size(); frame(9000); });
  if (reduced) { frame(9000); return; }
  let last = 0;
  requestAnimationFrame(function loop(now) {
    if (now - last > 50) { last = now; frame(now); }
    requestAnimationFrame(loop);
  });
})();
