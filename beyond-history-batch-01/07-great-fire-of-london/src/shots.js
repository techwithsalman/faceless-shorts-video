// Beyond History: The Great Fire of London Choreography Engine
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

  // Tailored Choreographies for The Great Fire of London
  const CAMERAS = [
    // 0: Bakery spark hook (Macro push-in on glowing ember erupting into flame)
    (k, t) => ({
      zoom: lerp(1.05, 1.25, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(0.015, -0.015, k),
      focus: 0.7,
      time: t,
    }),

    // 1: Timber firestorm (Upward tracking shot along flaming Tudor eaves with ember flurry)
    (k, t) => ({
      zoom: lerp(1.04, 1.16, k),
      panX: lerp(0.02, -0.02, k),
      panY: lerp(0.02, -0.015, k),
      focus: 0.5,
      time: t,
    }),

    // 2: Thames river evacuation (Gliding nautical pan across water reflecting burning city)
    (k, t) => {
      const waterLap = Math.sin(t * 2.2) * 0.003;
      return {
        zoom: lerp(1.03, 1.15, k),
        panX: lerp(-0.02, 0.02, k),
        panY: lerp(-0.01, 0.01, k) + waterLap,
        focus: 0.45,
        time: t,
      };
    },

    // 3: Old St Paul's melting lead roof (Dramatic vertical tilt down from gothic spires to molten lead)
    (k, t) => ({
      zoom: lerp(1.05, 1.18, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(-0.02, 0.02, k),
      focus: 0.6,
      time: t,
    }),

    // 4: Gunpowder firebreak detonation (High impact push-in with violent shockwave shake)
    (k, t) => {
      const blast = (k < 0.15) ? Math.sin(t * 30.0) * 0.007 * (1.0 - k / 0.15) : 0.0;
      return {
        zoom: lerp(1.06, 1.22, k),
        panX: lerp(-0.01, 0.01, k) + blast,
        panY: lerp(0.01, -0.01, k) + blast,
        focus: 0.55,
        time: t,
      };
    },

    // 5: Christopher Wren stone dome finale (Majestic pull-back into bright morning sky)
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

        // Firestorm Transitions
        if (i === 1 && lt < 0.22) {
          // Fiery orange blaze wash
          const alpha = (1 - lt / 0.22) * 0.55;
          ctx.fillStyle = `rgba(255, 110, 10, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.25) {
          // Thick black chimney smoke dissolve
          const alpha = (1 - lt / 0.25) * 0.45;
          ctx.fillStyle = `rgba(20, 15, 15, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.25) {
          // Molten glowing lead highlight
          const alpha = (1 - lt / 0.25) * 0.40;
          ctx.fillStyle = `rgba(255, 190, 80, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.20) {
          // Gunpowder smoke blast flash
          const alpha = (1 - lt / 0.20) * 0.50;
          ctx.fillStyle = `rgba(180, 160, 140, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.35) {
          // Clean London morning dawn sunlight
          const alpha = (1 - lt / 0.35) * 0.45;
          ctx.fillStyle = `rgba(245, 240, 230, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        if (t > T.dur - 0.5) {
          const fade = clamp((t - (T.dur - 0.5)) / 0.45);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Synchronized Sound Cues for The Great Fire of London
    if (i === 0) {
      cue(0.00, 'cinematic_impact', { gain: 0.95 });
      cue(0.05, 'slam', { gain: 0.85 });
      cue(0.20, 'foley_fire_crackle', { dur: 6.0, gain: 0.70 });
    } else if (i === 1) {
      cue(cut(1), 'whoosh', { gain: 0.75 });
      cue(cut(1) + 0.1, 'foley_fire_crackle', { dur: 6.5, gain: 0.65 });
    } else if (i === 2) {
      cue(cut(2), 'slide', { dur: 4.5, gain: 0.55 }); // Water lapping oars
      cue(cut(2) + 0.15, 'bell_toll', { dur: 5.5, gain: 0.50 });
    } else if (i === 3) {
      cue(cut(3), 'sub_drop', { gain: 0.75 });
      cue(cut(3) + 0.1, 'slam', { gain: 0.85 });
    } else if (i === 4) {
      cue(cut(4), 'cinematic_impact', { gain: 1.0 }); // Gunpowder boom
      cue(cut(4) + 0.05, 'slam', { gain: 0.95 });
    } else if (i === 5) {
      cue(cut(5), 'triumph_brass', { dur: 5.0, gain: 0.85 });
      cue(cut(5) + 0.2, 'bell_toll', { dur: 6.0, gain: 0.60 });
    }
  }

  return { shots: S, cues: CUES };
}
