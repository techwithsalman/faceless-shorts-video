// Beyond History: Pompeii Choreography Engine
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

  // Tailored Choreographies for Pompeii: Eruption, Cataclysm, and Silent Ruins
  const CAMERAS = [
    // 0: Vesuvius explosion hook (Low angle dynamic push-in with seismic rumble vibration)
    (k, t) => {
      const quake = Math.sin(t * 18.0) * 0.003 * (1.0 - k * 0.5);
      return {
        zoom: lerp(1.02, 1.15, k),
        panX: lerp(-0.01, 0.01, k) + quake,
        panY: lerp(0.02, -0.015, k) + quake,
        focus: 0.35,
        time: t,
      };
    },

    // 1: Street pelted by pumice (Downward tracking shot following citizens through darkness)
    (k, t) => ({
      zoom: lerp(1.04, 1.16, k),
      panX: lerp(0.02, -0.02, k),
      panY: lerp(-0.02, 0.015, k),
      focus: 0.5,
      time: t,
    }),

    // 2: Pyroclastic surge avalanche (Aggressive terrifying forward push + shockwave tremor)
    (k, t) => {
      const shockwave = (k < 0.12) ? Math.sin(t * 28.0) * 0.006 * (1.0 - k / 0.12) : 0.0;
      return {
        zoom: lerp(1.05, 1.25, k),
        panX: lerp(-0.015, 0.015, k) + shockwave,
        panY: lerp(0.01, -0.01, k) + shockwave,
        focus: 0.6,
        time: t,
      };
    },

    // 3: Buried silent ruins (Mournful slow horizontal pan across ruined columns under mist)
    (k, t) => ({
      zoom: lerp(1.10, 1.03, k),
      panX: lerp(-0.025, 0.025, k),
      panY: lerp(0.01, -0.01, k),
      focus: 0.4,
      time: t,
    }),

    // 4: Plaster cast of victim (Poignant macro rotational push-in on authentic plaster details)
    (k, t) => ({
      zoom: lerp(1.04, 1.18, k),
      panX: lerp(0.015, -0.01, k),
      panY: lerp(0.012, -0.015, k),
      focus: 0.7,
      time: t,
    }),

    // 5: Preserved Forum finale (Epic majestic pull-back towards Mount Vesuvius at sunset)
    (k, t) => ({
      zoom: lerp(1.18, 1.04, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(-0.015, 0.015, k),
      focus: 0.45,
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

        // Volcanic Atmospheric Transitions
        if (i === 1 && lt < 0.25) {
          // Ash cloud obscuration
          const alpha = (1 - lt / 0.25) * 0.45;
          ctx.fillStyle = `rgba(30, 25, 20, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.22) {
          // Incandescent fiery orange flash (pyroclastic surge ignition)
          const alpha = (1 - lt / 0.22) * 0.55;
          ctx.fillStyle = `rgba(255, 120, 20, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.30) {
          // Grey volcanic ash haze settling
          const alpha = (1 - lt / 0.30) * 0.40;
          ctx.fillStyle = `rgba(60, 60, 65, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.25) {
          // Soft archaeological spotlight warmth
          const alpha = (1 - lt / 0.25) * 0.30;
          ctx.fillStyle = `rgba(240, 220, 180, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.35) {
          // Golden Italian sunset swell
          const alpha = (1 - lt / 0.35) * 0.40;
          ctx.fillStyle = `rgba(255, 210, 130, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        // Outro fade to black in the final 0.5 seconds
        if (t > T.dur - 0.5) {
          const fade = clamp((t - (T.dur - 0.5)) / 0.45);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Synchronized Sound Cues for Pompeii
    if (i === 0) {
      cue(0.00, 'cinematic_impact', { gain: 1.0 });
      cue(0.05, 'slam', { gain: 0.9 });
      cue(0.20, 'foley_fire_crackle', { dur: 6.5, gain: 0.65 });
    } else if (i === 1) {
      cue(cut(1), 'whoosh', { gain: 0.65 });
      cue(cut(1) + 0.1, 'slide', { dur: 4.5, gain: 0.60 });
    } else if (i === 2) {
      cue(cut(2), 'sub_drop', { gain: 0.85 });
      cue(cut(2) + 0.05, 'slam', { gain: 0.95 });
      cue(cut(2) + 0.2, 'foley_winter_wind', { dur: 7.0, gain: 0.70 });
    } else if (i === 3) {
      cue(cut(3), 'bell_toll', { dur: 5.5, gain: 0.60 });
      cue(cut(3) + 0.15, 'foley_winter_wind', { dur: 6.0, gain: 0.40 });
    } else if (i === 4) {
      cue(cut(4), 'thud', { gain: 0.75 });
      cue(cut(4) + 0.2, 'bell_toll', { dur: 6.0, gain: 0.50 });
    } else if (i === 5) {
      cue(cut(5), 'triumph_brass', { dur: 5.0, gain: 0.80 });
      cue(cut(5) + 0.3, 'sub_drop', { gain: 0.65 });
    }
  }

  return { shots: S, cues: CUES };
}
