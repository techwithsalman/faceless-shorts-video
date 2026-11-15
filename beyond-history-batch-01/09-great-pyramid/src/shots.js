// Beyond History: The Great Pyramid of Giza Choreography Engine
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

  // Tailored Choreographies for The Great Pyramid
  const CAMERAS = [
    // 0: Impossible alignment hook (Majestic upward push toward gleaming polished white apex)
    (k, t) => ({
      zoom: lerp(1.03, 1.15, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(0.02, -0.015, k),
      focus: 0.35,
      time: t,
    }),

    // 1: Quarry workers hauling sledge (Tracking glide along strained workers and wooden ropes)
    (k, t) => ({
      zoom: lerp(1.04, 1.16, k),
      panX: lerp(-0.02, 0.02, k),
      panY: lerp(0.01, -0.01, k),
      focus: 0.55,
      time: t,
    }),

    // 2: Nile transport canal barge (Serene river tracking shot along white limestone blocks)
    (k, t) => {
      const riverFlow = Math.sin(t * 1.8) * 0.003;
      return {
        zoom: lerp(1.03, 1.14, k),
        panX: lerp(0.02, -0.02, k),
        panY: lerp(-0.01, 0.01, k) + riverFlow,
        focus: 0.45,
        time: t,
      };
    },

    // 3: Grand Gallery internal vault (Dramatic vertical tilt looking up soaring stone corbelling)
    (k, t) => ({
      zoom: lerp(1.05, 1.20, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(0.025, -0.02, k),
      focus: 0.65,
      time: t,
    }),

    // 4: Astronomical alignment twilight (Slow rotation under glittering circumpolar stars)
    (k, t) => ({
      zoom: lerp(1.04, 1.18, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(-0.01, 0.01, k),
      focus: 0.5,
      time: t,
    }),

    // 5: Giza plateau aerial finale (Epic majestic pull-back into golden Sahara desert horizon)
    (k, t) => ({
      zoom: lerp(1.20, 1.04, k),
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

        // Egyptian Golden Solar Transitions
        if (i === 1 && lt < 0.25) {
          // Blinding sun reflection flash off polished limestone
          const alpha = (1 - lt / 0.25) * 0.45;
          ctx.fillStyle = `rgba(255, 250, 235, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.25) {
          // Warm desert heat haze wash
          const alpha = (1 - lt / 0.25) * 0.40;
          ctx.fillStyle = `rgba(240, 205, 140, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.30) {
          // Dark subterranean tomb shadow dissolve
          const alpha = (1 - lt / 0.30) * 0.50;
          ctx.fillStyle = `rgba(15, 12, 10, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.28) {
          // Starry sapphire twilight bloom
          const alpha = (1 - lt / 0.28) * 0.45;
          ctx.fillStyle = `rgba(18, 24, 45, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.35) {
          // Golden pyramidion sunset glare
          const alpha = (1 - lt / 0.35) * 0.45;
          ctx.fillStyle = `rgba(255, 215, 110, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        if (t > T.dur - 0.5) {
          const fade = clamp((t - (T.dur - 0.5)) / 0.45);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Synchronized Sound Cues for The Great Pyramid
    if (i === 0) {
      cue(0.00, 'cinematic_impact', { gain: 1.0 });
      cue(0.05, 'sub_drop', { gain: 0.85 });
      cue(0.20, 'foley_winter_wind', { dur: 6.0, gain: 0.45 });
    } else if (i === 1) {
      cue(cut(1), 'thud', { gain: 0.80 }); // Sledge impact
      cue(cut(1) + 0.1, 'slide', { dur: 5.0, gain: 0.60 }); // Sledge sliding
    } else if (i === 2) {
      cue(cut(2), 'slide', { dur: 4.5, gain: 0.50 });
      cue(cut(2) + 0.15, 'bell_toll', { dur: 5.5, gain: 0.45 });
    } else if (i === 3) {
      cue(cut(3), 'sub_drop', { gain: 0.80 });
      cue(cut(3) + 0.1, 'foley_fire_crackle', { dur: 6.0, gain: 0.55 });
    } else if (i === 4) {
      cue(cut(4), 'bell_toll', { dur: 6.5, gain: 0.60 });
      cue(cut(4) + 0.2, 'foley_winter_wind', { dur: 6.0, gain: 0.40 });
    } else if (i === 5) {
      cue(cut(5), 'triumph_brass', { dur: 6.0, gain: 0.85 });
      cue(cut(5) + 0.3, 'sub_drop', { gain: 0.70 });
    }
  }

  return { shots: S, cues: CUES };
}
