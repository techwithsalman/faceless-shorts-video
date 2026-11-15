// Beyond History: The Samurai Choreography Engine
import { ctx, W, H, clamp, lerp, eio } from './core/lib.js';
import { T, L } from './core/timing.js';
import { drawAtmosphere } from './core/atmosphere.js';
import { DepthParallaxEngine } from './core/depthParallax.js';

const parallax = new DepthParallaxEngine(W, H);

export function buildShots(images, depths = [], script = {}) {
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.04);

  const lines = (script && script.lines) || [];
  const numLines = Math.max(lines.length, 1);

  function render25D(image, depth, { zoom = 1.0, panX = 0, panY = 0, focus = 0.5, time = 0.0 }) {
    if (!image) return;

    if (parallax && parallax.gl) {
      const glCanvas = parallax.render(image, depth, { panX, panY, zoom, focus, time });
      if (glCanvas) {
        ctx.save();
        ctx.drawImage(glCanvas, 0, 0, W, H);
        ctx.restore();
        return;
      }
    }

    ctx.save();
    ctx.fillStyle = '#0B0B0E';
    ctx.fillRect(0, 0, W, H);
    const targetAspect = W / H;
    const imgAspect = image.width / image.height;
    let baseW, baseH;
    if (imgAspect > targetAspect) {
      baseH = image.height;
      baseW = image.height * targetAspect;
    } else {
      baseW = image.width;
      baseH = image.width / targetAspect;
    }

    const z = Math.max(zoom, 1.0);
    const srcW = baseW / z, srcH = baseH / z;
    const cx = image.width * 0.5 + panX * image.width * 0.5;
    const cy = image.height * 0.5 + panY * image.height * 0.5;
    const sx = clamp(cx - srcW / 2, 0, Math.max(0, image.width - srcW));
    const sy = clamp(cy - srcH / 2, 0, Math.max(0, image.height - srcH));

    ctx.drawImage(image, sx, sy, srcW, srcH, 0, 0, W, H);
    ctx.restore();
  }

  // Tailored Choreographies for The Samurai
  const CAMERAS = [
    // 0: Katana draw macro hook (Extreme macro glide along razor-sharp tamahagane steel)
    (k, t) => ({
      zoom: lerp(1.06, 1.25, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(0.01, -0.01, k),
      focus: 0.7,
      time: t,
    }),

    // 1: Swordsmith forge (Low angle upward push through glowing sparks and smoke)
    (k, t) => ({
      zoom: lerp(1.04, 1.18, k),
      panX: lerp(0.02, -0.02, k),
      panY: lerp(0.02, -0.015, k),
      focus: 0.55,
      time: t,
    }),

    // 2: Bushido temple meditation (Peaceful zen lateral drift with falling cherry blossoms)
    (k, t) => ({
      zoom: lerp(1.03, 1.14, k),
      panX: lerp(-0.02, 0.02, k),
      panY: lerp(-0.01, 0.01, k),
      focus: 0.5,
      time: t,
    }),

    // 3: Sengoku battlefield march (Cadenced march tracking with fluttering war banners)
    (k, t) => {
      const marchStep = Math.sin(t * 7.5) * 0.003;
      return {
        zoom: lerp(1.04, 1.16, k),
        panX: lerp(-0.025, 0.025, k),
        panY: lerp(-0.005, 0.005, k) + marchStep,
        focus: 0.5,
        time: t,
      };
    },

    // 4: Musashi sunset duel (High contrast silhouette push toward blood-orange horizon)
    (k, t) => ({
      zoom: lerp(1.05, 1.20, k),
      panX: lerp(0.015, -0.015, k),
      panY: lerp(0.015, -0.01, k),
      focus: 0.6,
      time: t,
    }),

    // 5: Antique armor finale (Majestic pull-back inside sunlit tatami dojo into golden dust)
    (k, t) => ({
      zoom: lerp(1.18, 1.04, k),
      panX: lerp(0.01, -0.01, k),
      panY: lerp(-0.015, 0.015, k),
      focus: 0.4,
      time: t,
    }),
  ];

  for (let i = 0; i < numLines; i++) {
    const camFn = CAMERAS[i % CAMERAS.length];
    const imgForShot = Array.isArray(images) ? (images[i] || images[0]) : images;
    const depthForShot = Array.isArray(depths) ? (depths[i] || null) : null;
    const line = lines[i] || {};
    const note = line.visual || line.text || `Shot ${i + 1}`;

    add({
      id: `S${String(i + 1).padStart(2, '0')}`,
      at: cut(i),
      note,
      draw(lt, d, t) {
        const k = eio(clamp(lt / d));
        const cam = camFn(k, t);
        render25D(imgForShot, depthForShot, cam);
        drawAtmosphere(ctx, W, H, t);

        // Feudal Japanese Aesthetic Transitions
        if (i === 1 && lt < 0.22) {
          // Cold steel metallic reflection
          const alpha = (1 - lt / 0.22) * 0.45;
          ctx.fillStyle = `rgba(225, 235, 245, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.25) {
          // Forge fire ember orange glow
          const alpha = (1 - lt / 0.25) * 0.45;
          ctx.fillStyle = `rgba(255, 140, 30, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.28) {
          // Cherry blossom pink-amber bloom
          const alpha = (1 - lt / 0.28) * 0.35;
          ctx.fillStyle = `rgba(255, 230, 220, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.28) {
          // Morning battlefield mist wash
          const alpha = (1 - lt / 0.28) * 0.40;
          ctx.fillStyle = `rgba(35, 40, 45, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.35) {
          // Warm golden shoji morning light
          const alpha = (1 - lt / 0.35) * 0.42;
          ctx.fillStyle = `rgba(255, 230, 160, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        if (t > T.dur - 0.5) {
          const fade = clamp((t - (T.dur - 0.5)) / 0.45);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Synchronized Sound Cues for The Samurai
    if (i === 0) {
      cue(0.00, 'cinematic_impact', { gain: 0.95 });
      cue(0.05, 'whoosh', { gain: 0.85 }); // Katana draw ring
      cue(0.20, 'war_drum', { gain: 0.70 });
    } else if (i === 1) {
      cue(cut(1), 'thud', { gain: 0.85 }); // Anvil strike
      cue(cut(1) + 0.15, 'foley_fire_crackle', { dur: 5.5, gain: 0.60 });
    } else if (i === 2) {
      cue(cut(2), 'bell_toll', { dur: 6.0, gain: 0.60 }); // Temple bell
      cue(cut(2) + 0.2, 'foley_winter_wind', { dur: 5.0, gain: 0.40 });
    } else if (i === 3) {
      cue(cut(3), 'war_drum', { gain: 0.85 }); // Taiko drums
      cue(cut(3) + 0.1, 'slam', { gain: 0.75 });
    } else if (i === 4) {
      cue(cut(4), 'foley_war_horn', { dur: 5.0, gain: 0.80 });
      cue(cut(4) + 0.15, 'whoosh', { gain: 0.75 });
    } else if (i === 5) {
      cue(cut(5), 'triumph_brass', { dur: 5.5, gain: 0.85 });
      cue(cut(5) + 0.25, 'bell_toll', { dur: 6.5, gain: 0.55 });
    }
  }

  return { shots: S, cues: CUES };
}
