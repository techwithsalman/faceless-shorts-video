// Cinematic Atmospheric & Environmental Motion Engine
// Provides dynamic blizzard snow, swirling campfire embers, undulating river mist, and pulsating firelight.

const NUM_SNOW = 100;
const NUM_EMBERS = 50;

const snow = [];
for (let i = 0; i < NUM_SNOW; i++) {
  snow.push({
    x: (i * 79.3) % 1080,
    y: (i * 123.7) % 1920,
    r: 1.2 + ((i % 5) * 0.9),
    vx: -25 - ((i % 7) * 8.0), // Strong Danubian winter wind
    vy: 35 + ((i % 6) * 12.0),
    alpha: 0.35 + ((i % 4) * 0.18),
    wobble: 1.8 + (i % 4) * 0.6,
  });
}

const embers = [];
for (let i = 0; i < NUM_EMBERS; i++) {
  embers.push({
    x: 400 + ((i * 47.9) % 500),
    y: 1200 + ((i * 31.4) % 700),
    r: 1.5 + ((i % 4) * 0.8),
    vx: -15 + ((i % 5) * 7.0),
    vy: -45 - ((i % 6) * 15.0), // Buoyant rising sparks
    alpha: 0.5 + ((i % 4) * 0.15),
    wobble: 3.5 + (i % 3) * 1.2,
  });
}

export function drawAtmosphere(ctx, W, H, t) {
  ctx.save();

  // 1. Dynamic Campfire & Candle Pulse (Natural Illumination Fluctuation)
  const flk = 1.0 + 0.05 * Math.sin(t * 14.3) + 0.04 * Math.cos(t * 22.7) + 0.02 * Math.sin(t * 31.1);
  const glow = ctx.createRadialGradient(720, 1150, 40, 720, 1150, 850);
  glow.addColorStop(0, `rgba(255, 175, 70, ${0.14 * flk})`);
  glow.addColorStop(0.4, `rgba(220, 110, 30, ${0.06 * flk})`);
  glow.addColorStop(0.8, `rgba(160, 60, 10, ${0.02 * flk})`);
  glow.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, H);

  // 2. Volumetric Rolling Danube River Mist (Multi-Octave Drifting Fog Banks)
  const mistH = 550;
  const mistY = H - mistH;
  const fogDrift = Math.sin(t * 0.7) * 45;
  const mist = ctx.createLinearGradient(0, mistY, 0, H);
  const mistAlpha = 0.45 + 0.08 * Math.sin(t * 1.2);
  mist.addColorStop(0, 'rgba(40, 60, 90, 0)');
  mist.addColorStop(0.5, `rgba(30, 48, 75, ${0.22 * mistAlpha})`);
  mist.addColorStop(1, `rgba(15, 25, 45, ${0.60 * mistAlpha})`);
  ctx.fillStyle = mist;
  ctx.fillRect(0, mistY, W, mistH);

  // 3. Falling Winter Snow Particles (Diagonal Wind Streaks)
  for (let i = 0; i < NUM_SNOW; i++) {
    const s = snow[i];
    const px = (s.x + s.vx * t + Math.sin(t * s.wobble + i) * 35 + 21600) % W;
    const py = (s.y + s.vy * t + 38400) % H;
    const a = s.alpha * (0.8 + 0.2 * Math.sin(t * 2.5 + i));

    ctx.beginPath();
    ctx.arc(px, py, s.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(240, 245, 255, ${a})`;
    ctx.fill();
  }

  // 4. Rising Golden Campfire Embers & Sparks
  for (let i = 0; i < NUM_EMBERS; i++) {
    const e = embers[i];
    const px = (e.x + e.vx * t + Math.sin(t * e.wobble + i) * 45 + 21600) % W;
    const py = (e.y + e.vy * t + 38400) % H;
    const a = e.alpha * (0.6 + 0.4 * Math.sin(t * 4.5 + i));

    ctx.beginPath();
    ctx.arc(px, py, e.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 195, 75, ${a})`;
    ctx.shadowColor = 'rgba(255, 120, 20, 0.8)';
    ctx.shadowBlur = 6;
    ctx.fill();
  }
  ctx.shadowBlur = 0;

  // 5. Cinematic Lens Vignette (Soft Depth Border)
  const vig = ctx.createRadialGradient(W / 2, H / 2, 420, W / 2, H / 2, 1180);
  vig.addColorStop(0, 'rgba(0, 0, 0, 0)');
  vig.addColorStop(0.65, 'rgba(0, 0, 0, 0.22)');
  vig.addColorStop(1, 'rgba(0, 0, 0, 0.88)');
  ctx.fillStyle = vig;
  ctx.fillRect(0, 0, W, H);

  ctx.restore();
}
