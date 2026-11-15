// Beyond History: Modular Cinematic Historical Documentary Scene Engine
// Continuous organic motion, marching dynamics, 3D depth parallax, and character consistency
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

  // Render routine supporting WebGL true depth-displaced parallax with continuous living motion
  function render25D(image, depth, { zoom = 1.0, panX = 0, panY = 0, focus = 0.5, time = 0.0 }) {
    if (!image) return;

    // 1. Try WebGL Depth-Displacement Parallax Shader with Living Organic Motion
    if (parallax && parallax.gl) {
      const glCanvas = parallax.render(image, depth, {
        panX,
        panY,
        zoom,
        focus,
        time,
      });
      if (glCanvas) {
        ctx.save();
        ctx.drawImage(glCanvas, 0, 0, W, H);
        ctx.restore();
        return;
      }
    }

    // 2. Fallback: 2D Canvas with Aspect-Ratio "Cover" Math (Zero Stretching)
    ctx.save();
    ctx.fillStyle = '#0B0B0E';
    ctx.fillRect(0, 0, W, H);

    const targetAspect = W / H; // 1080 / 1920 = 0.5625
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
    const srcW = baseW / z;
    const srcH = baseH / z;
    const cx = image.width * 0.5 + panX * image.width * 0.5;
    const cy = image.height * 0.5 + panY * image.height * 0.5;
    const sx = clamp(cx - srcW / 2, 0, Math.max(0, image.width - srcW));
    const sy = clamp(cy - srcH / 2, 0, Math.max(0, image.height - srcH));

    ctx.drawImage(image, sx, sy, srcW, srcH, 0, 0, W, H);
    ctx.restore();
  }

  // Cinematic Choreographies: Varied camera framing and living depth
  const CAMERAS = [
    // 0: Wide Danubian camp establishing shot (slow push-in with river mist glide)
    (k, t) => ({
      zoom: lerp(1.02, 1.12, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(-0.015, 0.015, k),
      focus: 0.35,
      time: t,
    }),

    // 1: Roman Legion Marching (Continuous forward track + rhythmic footfall bobbing)
    (k, t) => {
      const marchBob = Math.sin(t * 7.5) * 0.0035; // Rhythmic soldier footfall cadence
      return {
        zoom: lerp(1.03, 1.16, k),
        panX: lerp(-0.025, 0.025, k),
        panY: lerp(-0.005, 0.005, k) + marchBob,
        focus: 0.55,
        time: t,
      };
    },

    // 2: Living Marcus Aurelius Portrait (Living human breathing micro-sway + perspective tilt)
    (k, t) => ({
      zoom: lerp(1.04, 1.15, k),
      panX: lerp(0.015, -0.015, k),
      panY: lerp(0.018, -0.018, k),
      focus: 0.5,
      time: t,
    }),

    // 3: Command Tent & Writing Desk (Slow push towards papyrus scroll and candle glow)
    (k, t) => ({
      zoom: lerp(1.18, 1.30, k),
      panX: lerp(-0.01, 0.01, k),
      panY: lerp(-0.01, 0.015, k),
      focus: 0.6,
      time: t,
    }),

    // 4: Mind Mastery Macro Close-up (Macro eye focus with micro-parallax and candle flicker)
    (k, t) => ({
      zoom: lerp(1.05, 1.18, k),
      panX: lerp(-0.015, 0.015, k),
      panY: lerp(0.005, -0.005, k),
      focus: 0.65,
      time: t,
    }),

    // 5: Contemplation of Fear (Wide command tent glide revealing night fires)
    (k, t) => ({
      zoom: lerp(1.10, 1.03, k),
      panX: lerp(0.02, -0.02, k),
      panY: lerp(-0.01, 0.01, k),
      focus: 0.45,
      time: t,
    }),

    // 6: Imperial Legacy Outro (Majestic slow pull-back bathed in dawn morning light)
    (k, t) => ({
      zoom: lerp(1.16, 1.04, k),
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

        // Organic Visual Transitions:
        // Shot 0: Immediate visual hook (NO fade from black, instant full brightness)
        if (i === 1 && lt < 0.25) {
          // Shot 1: Cold Danubian blizzard wind sweep
          const alpha = (1 - lt / 0.25) * 0.35;
          ctx.fillStyle = `rgba(210, 225, 240, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 2 && lt < 0.20) {
          // Shot 2: Freezing rain & mud atmospheric vignette
          const alpha = (1 - lt / 0.20) * 0.38;
          ctx.fillStyle = `rgba(10, 15, 20, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 3 && lt < 0.32) {
          // Shot 3: Entering warm candlelit tent (warm amber light leak)
          const alpha = (1 - lt / 0.32) * 0.38;
          ctx.fillStyle = `rgba(245, 160, 50, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 4 && lt < 0.28) {
          // Shot 4: Golden illumination flare (philosophical realization)
          const alpha = (1 - lt / 0.28) * 0.42;
          ctx.fillStyle = `rgba(255, 220, 110, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 5 && lt < 0.20) {
          // Shot 5: Stoic shadow cross-dissolve
          const alpha = (1 - lt / 0.20) * 0.35;
          ctx.fillStyle = `rgba(12, 12, 16, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        } else if (i === 6 && lt < 0.38) {
          // Shot 6: Majestic dawn sunlight swell
          const alpha = (1 - lt / 0.38) * 0.45;
          ctx.fillStyle = `rgba(255, 242, 215, ${alpha})`;
          ctx.fillRect(0, 0, W, H);
        }

        // Outro fade to black in the final 0.8 seconds of video
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
      cue(0.05, 'foley_winter_wind', { dur: 6.2, gain: 0.55 });
    } else if (i === 1) {
      cue(cut(1), 'foley_war_horn', { dur: 3.5, gain: 0.70 });
      cue(cut(1) + 0.1, 'foley_snow_march', { dur: 6.2, gain: 0.65 });
    } else if (i === 2) {
      cue(cut(2), 'sub_drop', { gain: 0.60 });
      cue(cut(2) + 0.1, 'foley_winter_wind', { dur: 4.8, gain: 0.50 });
    } else if (i === 3) {
      cue(cut(3), 'foley_fire_crackle', { dur: 5.0, gain: 0.60 });
      cue(cut(3) + 0.25, 'foley_quill_scratch', { dur: 4.5, gain: 0.55 });
    } else if (i === 4) {
      cue(cut(4), 'cinematic_impact', { gain: 0.85 });
      cue(cut(4) + 0.1, 'foley_fire_crackle', { dur: 5.5, gain: 0.50 });
    } else if (i === 5) {
      cue(cut(5), 'war_drum', { gain: 0.75 });
      cue(cut(5) + 0.1, 'foley_winter_wind', { dur: 4.2, gain: 0.45 });
    } else if (i === 6) {
      cue(cut(6), 'triumph_brass', { dur: 4.0, gain: 0.70 });
      cue(cut(6) + 0.2, 'bell_toll', { dur: 5.5, gain: 0.55 });
    }
  }

  return { shots: S, cues: CUES };
}
