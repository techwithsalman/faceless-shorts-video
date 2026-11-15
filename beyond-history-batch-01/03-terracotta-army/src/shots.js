// Beyond History: The Terracotta Army Documentary Choreography Engine
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

  // Tailored Choreographies for The Terracotta Army
  const CAMERAS = [
    // 0: Shovel striking clay head in dirt pit (Dynamic discovery push)
    (k, t) => ({
      zoom: lerp(1.03, 1.15, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(-0.01, 0.015, k),
      focus: 0.45,
      time: t,
    }),

    // 1: Vast subterranean army corridor (Tracking across rows of clay infantry)
    (k, t) => ({
      zoom: lerp(1.04, 1.16, k),
      panX: lerp(-0.02, 0.02, k),
      panY: lerp(-0.005, 0.005, k),
      focus: 0.5,
      time: t,
    }),

    // 2: Macro panning across unique warrior faces (Micro-detail focus)
    (k, t) => ({
      zoom: lerp(1.06, 1.20, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(0.005, -0.005, k),
      focus: 0.7,
      time: t,
    }),

    // 3: Emperor Qin Shi Huang in imperial palace (Living human breathing micro-sway)
    (k, t) => ({
      zoom: lerp(1.05, 1.18, k),
      panX: lerp(0.015, -0.015, k),
      panY: lerp(0.01, -0.01, k),
      focus: 0.6,
      time: t,
    }),

    // 4: Underground mercury rivers chamber (Slow glide through eerie subterranean mist)
    (k, t) => ({
      zoom: lerp(1.15, 1.04, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(-0.01, 0.01, k),
      focus: 0.45,
      time: t,
    }),

    // 5: Solitary Terracotta General eternal vigil (Epic documentary pull-back)
    (k, t) => ({
      zoom: lerp(1.16, 1.03, k),
      panX: lerp(0.015, -0.015, k),
      panY: lerp(-0.012, 0.01, k),
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

        // Organic Transitions
        if (i === 1 && lt < 0.25) {
          // Archaeological dust dissolve
          const alpha = (1 - lt / 0.25) * 0.38;
          ctx.fillStyle = `rgba(225, 205, 175, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.22) {
          // Terracotta clay warmth dissolve
          const alpha = (1 - lt / 0.22) * 0.35;
          ctx.fillStyle = `rgba(210, 160, 120, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.28) {
          // Imperial black & crimson cross-fade
          const alpha = (1 - lt / 0.28) * 0.42;
          ctx.fillStyle = `rgba(20, 10, 10, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.26) {
          // Silvery mercury glow transition
          const alpha = (1 - lt / 0.26) * 0.40;
          ctx.fillStyle = `rgba(160, 210, 220, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.35) {
          // Golden spotlight swell
          const alpha = (1 - lt / 0.35) * 0.45;
          ctx.fillStyle = `rgba(255, 225, 160, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        // Outro fade to black
        if (t > T.dur - 0.8) {
          const fade = clamp((t - (T.dur - 0.8)) / 0.7);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Sound Cues
    if (i === 0) {
      cue(0.00, 'foley_shovel_strike', { gain: 0.95 });
      cue(0.08, 'sub_drop', { gain: 0.60 });
    } else if (i === 1) {
      cue(cut(1), 'cinematic_impact', { gain: 0.85 });
      cue(cut(1) + 0.15, 'foley_ancient_halls', { dur: 6.0, gain: 0.50 });
    } else if (i === 2) {
      cue(cut(2), 'foley_clay_clink', { dur: 3.5, gain: 0.55 });
      cue(cut(2) + 0.2, 'foley_dust_whisper', { dur: 4.5, gain: 0.45 });
    } else if (i === 3) {
      cue(cut(3), 'guzheng_pluck', { dur: 4.0, gain: 0.65 });
      cue(cut(3) + 0.15, 'foley_palace_fire', { dur: 5.5, gain: 0.50 });
    } else if (i === 4) {
      cue(cut(4), 'foley_mercury_drip', { dur: 5.0, gain: 0.60 });
      cue(cut(4) + 0.1, 'sub_drop', { gain: 0.70 });
    } else if (i === 5) {
      cue(cut(5), 'chinese_bell', { dur: 5.5, gain: 0.65 });
      cue(cut(5) + 0.2, 'triumph_brass', { dur: 4.5, gain: 0.70 });
    }
  }

  return { shots: S, cues: CUES };
}
