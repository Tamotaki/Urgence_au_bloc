
// ── Pluie hexadécimale (Matrix rouge) ──────────────────────────────────────
(function() {
  const canvas = document.getElementById('matrix-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, drops;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
    const cols = Math.floor(W / 16);
    drops = Array.from({length: cols}, () => Math.random() * -50);
  }
  window.addEventListener('resize', resize);
  resize();

  const chars = '0123456789ABCDEF'.split('');
  function draw() {
    ctx.fillStyle = 'rgba(5,0,0,0.06)';
    ctx.fillRect(0, 0, W, H);
    ctx.font = '13px Share Tech Mono, monospace';
    drops.forEach((y, i) => {
      const c = chars[Math.floor(Math.random() * chars.length)];
      const alpha = Math.random() > 0.85 ? 1 : 0.4;
      ctx.fillStyle = `rgba(180,0,30,${alpha})`;
      ctx.fillText(c, i * 16, y * 16);
      if (y * 16 > H && Math.random() > 0.975) drops[i] = 0;
      drops[i] += 0.5;
    });
  }
  setInterval(draw, 50);
})();

// ── Grille hex animée ───────────────────────────────────────────────────────
(function() {
  const grid = document.getElementById('hex-grid');
  if (!grid) return;
  const HEX = '0123456789ABCDEF';
  const COUNT = 480;
  const cells = [];
  for (let i = 0; i < COUNT; i++) {
    const span = document.createElement('span');
    span.className = 'hex-cell';
    span.textContent = HEX[Math.floor(Math.random()*16)] + HEX[Math.floor(Math.random()*16)] + ' ';
    grid.appendChild(span);
    cells.push(span);
  }
  setInterval(() => {
    const idx = Math.floor(Math.random() * COUNT);
    cells[idx].textContent = HEX[Math.floor(Math.random()*16)] + HEX[Math.floor(Math.random()*16)] + ' ';
    cells[idx].classList.add('active');
    setTimeout(() => cells[idx].classList.remove('active'), 300);
  }, 40);
})();

// ── Compte à rebours ────────────────────────────────────────────────────────
(function() {
  const el = document.getElementById('countdown-inline');
  if (!el) return;
  const KEY = 'ransom_deadline';
  let deadline = localStorage.getItem(KEY);
  if (!deadline) {
    deadline = Date.now() + 23 * 3600000 + 59 * 60000 + 59000;
    localStorage.setItem(KEY, deadline);
  } else {
    deadline = parseInt(deadline);
  }
  function update() {
    const left = Math.max(0, deadline - Date.now());
    const h = String(Math.floor(left / 3600000)).padStart(2,'0');
    const m = String(Math.floor((left % 3600000) / 60000)).padStart(2,'0');
    const s = String(Math.floor((left % 60000) / 1000)).padStart(2,'0');
    el.textContent = `${h}:${m}:${s}`;
    if (left === 0) el.textContent = '00:00:00';
  }
  update();
  setInterval(update, 1000);
})();

// ── Glitch aléatoire sur le titre ───────────────────────────────────────────
(function() {
  const title = document.querySelector('.ransom-title');
  if (!title) return;
  const original = title.textContent;
  const CHARS = 'X#@$%!?0123456789ABCDEF';
  setInterval(() => {
    if (Math.random() > 0.7) {
      let scrambled = '';
      for (let c of original) {
        scrambled += Math.random() > 0.85
          ? CHARS[Math.floor(Math.random() * CHARS.length)] : c;
      }
      title.textContent = scrambled;
      setTimeout(() => title.textContent = original, 120);
    }
  }, 800);
})();
