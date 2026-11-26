// The animation of the hero: commits travel from the source through the
// local mirror to the destination. It is decoration: it draws at 30 frames
// per second at most, stops while it is out of sight, and is a still
// picture for readers who asked for reduced motion.

const W = 900;
const H = 420;
const FPS = 30;
const NODES = [
  { x: 130, name: "source", color: "--c2" },
  { x: 450, name: "local mirror", color: "--muted" },
  { x: 770, name: "destination", color: "--c3" },
];
const LANES = 7;
const COMMITS = 30;
const MID = H / 2 - 22;

const smooth = (t) => t * t * (3 - 2 * t);

// The position on a lane: t runs from 0 at the source over 1 at the mirror
// to 2 at the destination. Lanes fan out in the middle of each leg.
function point(lane, t) {
  const leg = Math.min(1, Math.floor(t));
  const local = t - leg;
  const spread = (lane - (LANES - 1) / 2) * 44;
  const bulge = Math.sin(Math.PI * local);
  return [
    NODES[leg].x + (NODES[leg + 1].x - NODES[leg].x) * smooth(local),
    MID + spread * bulge,
  ];
}

function newCommit(anywhere) {
  return {
    lane: Math.floor(Math.random() * LANES),
    t: anywhere ? Math.random() * 2 : 0,
    speed: 0.1 + Math.random() * 0.12,
  };
}

export function createFlow(canvas) {
  const context = canvas.getContext("2d");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const commits = Array.from({ length: COMMITS }, () => newCommit(true));
  let colors = {};
  let running = false;
  let visible = true;
  let frame = 0;
  let last = 0;

  function readColors() {
    const style = getComputedStyle(document.documentElement);
    for (const name of ["--fg", "--muted", "--line", "--surface", "--c2", "--c3", "--signal"]) {
      colors[name] = style.getPropertyValue(name).trim();
    }
  }

  function resize() {
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    const box = canvas.getBoundingClientRect();
    canvas.width = Math.round(box.width * ratio);
    canvas.height = Math.round(box.height * ratio);
    context.setTransform(canvas.width / W, 0, 0, canvas.height / H, 0, 0);
  }

  function drawLanes() {
    context.lineWidth = 1;
    context.strokeStyle = colors["--line"];
    for (let lane = 0; lane < LANES; lane++) {
      context.beginPath();
      for (let step = 0; step <= 80; step++) {
        const [x, y] = point(lane, Math.min(1.9999, (step / 80) * 2));
        if (step) context.lineTo(x, y);
        else context.moveTo(x, y);
      }
      context.stroke();
    }
  }

  function drawNodes(time) {
    context.font = '500 20px "IBM Plex Mono", ui-monospace, monospace';
    context.textAlign = "center";
    for (const [index, node] of NODES.entries()) {
      const color = colors[node.color];
      if (running && index === 1) {
        // Rings leave the mirror while data passes through it.
        const phase = (time / 2.4) % 1;
        context.globalAlpha = 0.5 * (1 - phase);
        context.strokeStyle = colors["--signal"];
        context.lineWidth = 1.5;
        context.beginPath();
        context.arc(node.x, MID, 40 + 60 * phase, 0, Math.PI * 2);
        context.stroke();
        context.globalAlpha = 1;
      }
      context.fillStyle = colors["--surface"];
      context.strokeStyle = color;
      context.lineWidth = 2;
      context.beginPath();
      context.arc(node.x, MID, 40, 0, Math.PI * 2);
      context.fill();
      context.stroke();
      context.fillStyle = color;
      context.beginPath();
      context.arc(node.x, MID, index === 1 ? 7 : 13, 0, Math.PI * 2);
      context.fill();
      context.fillStyle = colors["--muted"];
      context.fillText(node.name, node.x, H - 30);
    }
  }

  function drawCommits(step) {
    context.lineCap = "round";
    context.lineWidth = 3.2;
    const pace = running ? 3.2 : 1;
    for (const commit of commits) {
      commit.t += commit.speed * pace * step;
      if (commit.t >= 2) Object.assign(commit, newCommit(false));
      const tail = Math.max(0, commit.t - 0.07);
      // A tail which would cross the mirror starts at the mirror.
      const from = Math.floor(tail) === Math.floor(commit.t) ? tail : Math.floor(commit.t);
      const [x0, y0] = point(commit.lane, from);
      const [x1, y1] = point(commit.lane, Math.min(1.9999, commit.t));
      const edge = Math.min(commit.t, 2 - commit.t);
      context.globalAlpha = Math.min(1, edge * 5) * (running ? 0.95 : 0.6);
      context.strokeStyle = running ? colors["--signal"] : colors[commit.t < 1 ? "--c2" : "--c3"];
      context.beginPath();
      context.moveTo(x0, y0);
      context.lineTo(x1, y1);
      context.stroke();
    }
    context.globalAlpha = 1;
  }

  function draw(time, step) {
    context.clearRect(0, 0, W, H);
    drawLanes();
    drawCommits(step);
    drawNodes(time);
  }

  function tick(now) {
    frame = 0;
    if (document.hidden || !visible) return;
    if (now - last >= 1000 / FPS - 1) {
      const step = last ? Math.min(0.1, (now - last) / 1000) : 1 / FPS;
      last = now;
      draw(now / 1000, step);
    }
    frame = requestAnimationFrame(tick);
  }

  function wake() {
    if (still) {
      draw(0, 0);
    } else if (!frame && !document.hidden && visible) {
      last = 0;
      frame = requestAnimationFrame(tick);
    }
  }

  readColors();
  resize();
  draw(0, 0);
  new ResizeObserver(() => {
    resize();
    draw(performance.now() / 1000, 0);
  }).observe(canvas);
  new IntersectionObserver((entries) => {
    visible = entries.some((entry) => entry.isIntersecting);
    wake();
  }).observe(canvas);
  document.addEventListener("visibilitychange", wake);
  window.addEventListener("themechange", () => {
    readColors();
    draw(performance.now() / 1000, 0);
  });
  // The fonts may arrive after the first frame.
  document.fonts?.ready.then(() => draw(performance.now() / 1000, 0));
  wake();

  return {
    setRunning(value) {
      running = value;
      if (still) draw(0, 0);
    },
  };
}
