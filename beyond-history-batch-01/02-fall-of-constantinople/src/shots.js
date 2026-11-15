// Beyond History: The Fall of Constantinople (1453) Documentary Choreography Engine
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

  // Tailored Choreographies for The Fall of Constantinople
  const CAMERAS = [
    // 0: Theodosian Walls at Night (Slow imposing push towards stone battlements)
    (k, t) => ({
      zoom: lerp(1.02, 1.14, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(-0.015, 0.015, k),
      focus: 0.35,
      time: t,
    }),

    // 1: Orban Super-Cannon Basilisk (Heavy recoil shake + push toward muzzle)
    (k, t) => {
      const recoilShake = k < 0.08 ? (Math.sin(t * 35.0) * 0.006 * (1 - k / 0.08)) : 0.0;
      return {
        zoom: lerp(1.05, 1.18, k),
        panX: lerp(0.01, -0.01, k) + recoilShake,
        panY: lerp(0.01, -0.01, k) + recoilShake,
        focus: 0.55,
        time: t,
      };
    },

    // 2: Overland Fleet Over Wooded Hills (Tracking across lines of oxen and galleys)
    (k, t) => ({
      zoom: lerp(1.03, 1.15, k),
      panX: lerp(-0.025, 0.025, k),
      panY: lerp(-0.005, 0.005, k),
      focus: 0.5,
      time: t,
    }),

    // 3: The Breach Assault (Dynamic charge push through Greek fire smoke)
    (k, t) => {
      const battleJolts = Math.sin(t * 8.0) * 0.0025;
      return {
        zoom: lerp(1.04, 1.18, k),
        panX: lerp(-0.015, 0.015, k),
        panY: lerp(-0.01, 0.01, k) + battleJolts,
        focus: 0.6,
        time: t,
      };
    },

    // 4: Emperor Constantine XI Last Stand (Living human breathing micro-sway + grief resolve)
    (k, t) => ({
      zoom: lerp(1.06, 1.22, k),
      panX: lerp(0.015, -0.015, k),
      panY: lerp(0.01, -0.01, k),
      focus: 0.7,
      time: t,
    }),

    // 5: Hagia Sophia Dawn Outro (Epic slow pull-back as dawn sunlight breaks over domes)
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

        // Organic Cinematic Transitions:
        // Shot 0: Immediate visual hook (frame 0 full brightness)
        if (i === 1 && lt < 0.28) {
          // Shot 1: Blinding cannon muzzle flash
          const alpha = (1 - lt / 0.28) * 0.48;
          ctx.fillStyle = `rgba(255, 140, 50, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.24) {
          // Shot 2: Torchlight night woodland glide
          const alpha = (1 - lt / 0.24) * 0.38;
          ctx.fillStyle = `rgba(230, 130, 40, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.30) {
          // Shot 3: Greek fire explosion flash
          const alpha = (1 - lt / 0.30) * 0.45;
          ctx.fillStyle = `rgba(180, 255, 70, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.25) {
          // Shot 4: Battle smoke & blood vignette dissolve
          const alpha = (1 - lt / 0.25) * 0.40;
          ctx.fillStyle = `rgba(25, 10, 10, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.38) {
          // Shot 5: Golden-pink Byzantine dawn sunlight swell
          const alpha = (1 - lt / 0.38) * 0.45;
          ctx.fillStyle = `rgba(255, 220, 210, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        // Outro fade to black in the final 0.8 seconds
        if (t > T.dur - 0.8) {
          const fade = clamp((t - (T.dur - 0.8)) / 0.7);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Synchronized Documentary Sound Cues
    if (i === 0) {
      cue(0.00, 'cinematic_impact', { gain: 0.95 });
      cue(0.08, 'foley_siege_wind', { dur: 6.0, gain: 0.45 });
    } else if (i === 1) {
      cue(cut(1), 'foley_cannon_blast', { dur: 3.5, gain: 0.95 });
      cue(cut(1) + 0.3, 'foley_stone_collapse', { dur: 4.5, gain: 0.70 });
    } else if (i === 2) {
      cue(cut(2), 'foley_galley_rollers', { dur: 5.5, gain: 0.65 });
      cue(cut(2) + 0.2, 'foley_siege_wind', { dur: 4.5, gain: 0.40 });
    } else if (i === 3) {
      cue(cut(3), 'war_drum', { gain: 0.85 });
      cue(cut(3) + 0.15, 'foley_greek_fire', { dur: 5.0, gain: 0.65 });
    } else if (i === 4) {
      cue(cut(4), 'cinematic_impact', { gain: 0.90 });
      cue(cut(4) + 0.1, 'foley_sword_draw', { dur: 2.5, gain: 0.65 });
    } else if (i === 5) {
      cue(cut(5), 'byzantine_bell', { dur: 5.5, gain: 0.65 });
      cue(cut(5) + 0.2, 'triumph_brass', { dur: 4.5, gain: 0.70 });
    }
  }

  return { shots: S, cues: CUES };
}
