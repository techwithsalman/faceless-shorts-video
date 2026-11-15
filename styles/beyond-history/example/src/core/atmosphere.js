// Cinematic atmosphere: dynamic particles, candle flicker, smoke haze, and vignette
const NUM_PARTICLES = 45;
const particles = [];
for (let i = 0; i < NUM_PARTICLES; i++) {
  particles.push({
    x: ((i * 137.5) % 1080),
    y: ((i * 263.3) % 1920),
    r: 1.5 + ((i % 5) * 0.8),
    vx: -8 + ((i % 7) * 2.5),
    vy: 18 + ((i % 6) * 6),
    alpha: 0.25 + ((i % 4) * 0.18),
    warm: i % 3 === 0,
    wobble: 1.2 + (i % 4) * 0.5,
  });
}

export function drawAtmosphere(ctx, W, H, t) {
  ctx.save();

  // 1. Warm Candle / Campfire Ambient Flicker
  const flk = 1.0 + 0.04 * Math.sin(t * 14.3) + 0.03 * Math.cos(t * 22.7);
  const glow = ctx.createRadialGradient(880, 880, 50, 880, 880, 700);
  glow.addColorStop(0, `rgba(255, 180, 80, ${0.12 * flk})`);
  glow.addColorStop(0.5, `rgba(220, 120, 40, ${0.05 * flk})`);
  glow.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, H);

  // 2. Cold Frontier Mist at Bottom
  const mist = ctx.createLinearGradient(0, H - 450, 0, H);
  mist.addColorStop(0, 'rgba(40, 55, 80, 0)');
  mist.addColorStop(0.7, 'rgba(30, 45, 70, 0.25)');
  mist.addColorStop(1, 'rgba(20, 30, 50, 0.55)');
  ctx.fillStyle = mist;
  ctx.fillRect(0, H - 450, W, 450);

  // 3. Floating Dust & Embers
  for (let i = 0; i < NUM_PARTICLES; i++) {
    const p = particles[i];
    const px = (p.x + p.vx * t + Math.sin(t * p.wobble + i) * 24 + 10800) % W;
    const py = (p.y - p.vy * t + 19200) % H;
    const a = p.alpha * (0.7 + 0.3 * Math.sin(t * 3.1 + i));

    ctx.beginPath();
    ctx.arc(px, py, p.r, 0, Math.PI * 2);
    ctx.fillStyle = p.warm ? `rgba(255, 210, 120, ${a})` : `rgba(240, 240, 255, ${a * 0.7})`;
    ctx.fill();
  }

  // 4. Cinematic Lens Vignette
  const vig = ctx.createRadialGradient(W / 2, H / 2, 400, W / 2, H / 2, 1150);
  vig.addColorStop(0, 'rgba(0, 0, 0, 0)');
  vig.addColorStop(0.65, 'rgba(0, 0, 0, 0.25)');
  vig.addColorStop(1, 'rgba(0, 0, 0, 0.85)');
  ctx.fillStyle = vig;
  ctx.fillRect(0, 0, W, H);

  ctx.restore();
}
