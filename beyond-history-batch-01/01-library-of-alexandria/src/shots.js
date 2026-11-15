// Beyond History: The Library of Alexandria Documentary Choreography Engine
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

  // Tailored Choreographies for The Library of Alexandria
  const CAMERAS = [
    // 0: Grand Colonnaded Hall of Alexandria (Slow majestic push towards sunbeams)
    (k, t) => ({
      zoom: lerp(1.02, 1.14, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(-0.01, 0.015, k),
      focus: 0.4,
      time: t,
    }),

    // 1: Ptolemaic Harbor Scroll Confiscation (Tracking across merchant galleys and scribes)
    (k, t) => ({
      zoom: lerp(1.03, 1.15, k),
      panX: lerp(-0.02, 0.02, k),
      panY: lerp(0.005, -0.005, k),
      focus: 0.5,
      time: t,
    }),

    // 2: Julius Caesar's Burning Fleet (Dynamic dramatic push + heat shimmer)
    (k, t) => {
      const heatWobble = Math.sin(t * 12.0) * 0.002;
      return {
        zoom: lerp(1.05, 1.18, k),
        panX: lerp(0.015, -0.015, k),
        panY: lerp(-0.01, 0.01, k) + heatWobble,
        focus: 0.55,
        time: t,
      };
    },

    // 3: Decaying Colonnade & Neglect (Melancholic slow pull-back revealing cracked arches)
    (k, t) => ({
      zoom: lerp(1.15, 1.04, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(0.01, -0.01, k),
      focus: 0.45,
      time: t,
    }),

    // 4: Weathered Scholar Hands on Papyrus (Macro focus on fragile Greek lettering)
    (k, t) => ({
      zoom: lerp(1.06, 1.20, k),
      panX: lerp(0.01, -0.01, k),
      panY: lerp(-0.005, 0.005, k),
      focus: 0.7,
      time: t,
    }),

    // 5: Pharos Lighthouse at Sunset (Epic pull-back bathed in golden Mediterranean light)
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
        // Shot 0: Immediate visual hook (frame 0 visibility, NO black mask)
        if (i === 1 && lt < 0.25) {
          // Shot 1: Mediterranean morning sea breeze
          const alpha = (1 - lt / 0.25) * 0.35;
          ctx.fillStyle = `rgba(220, 240, 255, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.28) {
          // Shot 2: Fire flash transition (Caesar's fleet ablaze)
          const alpha = (1 - lt / 0.28) * 0.45;
          ctx.fillStyle = `rgba(255, 120, 40, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.22) {
          // Shot 3: Ash shadow vignette dissolve
          const alpha = (1 - lt / 0.22) * 0.38;
          ctx.fillStyle = `rgba(18, 14, 14, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.30) {
          // Shot 4: Warm oil lamp amber light leak
          const alpha = (1 - lt / 0.30) * 0.40;
          ctx.fillStyle = `rgba(250, 180, 60, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.38) {
          // Shot 5: Golden hour Mediterranean sunlight swell
          const alpha = (1 - lt / 0.38) * 0.45;
          ctx.fillStyle = `rgba(255, 235, 190, ${alpha})`;
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
      cue(0.08, 'foley_subtle_wind', { dur: 5.5, gain: 0.45 });
    } else if (i === 1) {
      cue(cut(1), 'foley_sea_waves', { dur: 6.0, gain: 0.55 });
      cue(cut(1) + 0.2, 'foley_wooden_creak', { dur: 3.5, gain: 0.50 });
    } else if (i === 2) {
      cue(cut(2), 'cinematic_impact', { gain: 0.90 });
      cue(cut(2) + 0.1, 'foley_fire_inferno', { dur: 6.2, gain: 0.65 });
    } else if (i === 3) {
      cue(cut(3), 'sub_drop', { gain: 0.60 });
      cue(cut(3) + 0.1, 'foley_dust_whisper', { dur: 5.0, gain: 0.45 });
    } else if (i === 4) {
      cue(cut(4), 'foley_quill_scratch', { dur: 5.0, gain: 0.60 });
      cue(cut(4) + 0.2, 'foley_fire_crackle', { dur: 6.0, gain: 0.45 });
    } else if (i === 5) {
      cue(cut(5), 'triumph_brass', { dur: 4.5, gain: 0.70 });
      cue(cut(5) + 0.2, 'bell_toll', { dur: 5.5, gain: 0.60 });
    }
  }

  return { shots: S, cues: CUES };
}
