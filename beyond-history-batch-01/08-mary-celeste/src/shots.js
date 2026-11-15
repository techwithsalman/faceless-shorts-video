// Beyond History: Mary Celeste Choreography Engine
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

  // Tailored Choreographies for Mary Celeste
  const CAMERAS = [
    // 0: Drifting brigantine hook (Swaying oceanic roll on choppy grey Atlantic swells)
    (k, t) => {
      const swell = Math.sin(t * 1.6) * 0.005;
      return {
        zoom: lerp(1.03, 1.15, k),
        panX: lerp(-0.015, 0.015, k),
        panY: lerp(-0.01, 0.01, k) + swell,
        focus: 0.35,
        time: t,
      };
    },

    // 1: Deserted wet deck (Forward track along wet planks past spinning ship wheel)
    (k, t) => ({
      zoom: lerp(1.04, 1.18, k),
      panX: lerp(0.02, -0.02, k),
      panY: lerp(0.015, -0.015, k),
      focus: 0.55,
      time: t,
    }),

    // 2: Captain's untouched cabin (Slow lateral pan across navigational chart and dividers)
    (k, t) => ({
      zoom: lerp(1.05, 1.20, k),
      panX: lerp(-0.02, 0.02, k),
      panY: lerp(-0.01, 0.01, k),
      focus: 0.65,
      time: t,
    }),

    // 3: Dark hold with alcohol barrels (Low angle glide past iron-strapped casks with vapor haze)
    (k, t) => ({
      zoom: lerp(1.04, 1.16, k),
      panX: lerp(0.015, -0.015, k),
      panY: lerp(0.02, -0.02, k),
      focus: 0.5,
      time: t,
    }),

    // 4: Doomed lifeboat storm (Turbulent wave roll and stormy camera tremor)
    (k, t) => {
      const stormTremor = Math.sin(t * 12.0) * 0.004;
      return {
        zoom: lerp(1.06, 1.22, k),
        panX: lerp(-0.02, 0.02, k) + stormTremor,
        panY: lerp(0.015, -0.015, k) + stormTremor,
        focus: 0.55,
        time: t,
      };
    },

    // 5: Ethereal foggy sea finale (Majestic pull-back as bow cuts through sunlit sea fog)
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

        // Maritime Mystery Transitions
        if (i === 1 && lt < 0.25) {
          // Atlantic sea spray wash
          const alpha = (1 - lt / 0.25) * 0.40;
          ctx.fillStyle = `rgba(180, 205, 220, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.25) {
          // Cabin interior shadow dissolve
          const alpha = (1 - lt / 0.25) * 0.45;
          ctx.fillStyle = `rgba(12, 16, 22, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.30) {
          // Bilge hold deep darkness
          const alpha = (1 - lt / 0.30) * 0.50;
          ctx.fillStyle = `rgba(5, 8, 12, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.22) {
          // Lightning strike flash
          const alpha = (1 - lt / 0.22) * 0.55;
          ctx.fillStyle = `rgba(220, 235, 255, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.35) {
          // Morning sea mist sunburst
          const alpha = (1 - lt / 0.35) * 0.45;
          ctx.fillStyle = `rgba(255, 240, 215, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        if (t > T.dur - 0.5) {
          const fade = clamp((t - (T.dur - 0.5)) / 0.45);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Synchronized Sound Cues for Mary Celeste
    if (i === 0) {
      cue(0.00, 'cinematic_impact', { gain: 0.95 });
      cue(0.05, 'slide', { dur: 5.5, gain: 0.60 }); // Creaking hull swells
      cue(0.20, 'foley_winter_wind', { dur: 6.0, gain: 0.50 });
    } else if (i === 1) {
      cue(cut(1), 'thud', { gain: 0.70 }); // Wet deck footfall
      cue(cut(1) + 0.1, 'slide', { dur: 4.5, gain: 0.55 });
    } else if (i === 2) {
      cue(cut(2), 'whoosh', { gain: 0.65 });
      cue(cut(2) + 0.15, 'bell_toll', { dur: 6.0, gain: 0.50 });
    } else if (i === 3) {
      cue(cut(3), 'sub_drop', { gain: 0.75 });
      cue(cut(3) + 0.1, 'slam', { gain: 0.80 }); // Barrel thud
    } else if (i === 4) {
      cue(cut(4), 'cinematic_impact', { gain: 1.0 }); // Thunderclap
      cue(cut(4) + 0.05, 'foley_winter_wind', { dur: 7.0, gain: 0.70 });
    } else if (i === 5) {
      cue(cut(5), 'triumph_brass', { dur: 5.5, gain: 0.80 });
      cue(cut(5) + 0.25, 'sub_drop', { gain: 0.65 });
    }
  }

  return { shots: S, cues: CUES };
}
