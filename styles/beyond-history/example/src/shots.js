// Beyond History: Modular Cinematic Historical Documentary Scene Engine
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

  // Render routine supporting WebGL true depth-displaced parallax with aspect-preserved cover
  function render25D(image, depth, { zoom = 1.0, panX = 0, panY = 0, focus = 0.5 }) {
    if (!image) return;

    // 1. Try WebGL Depth-Displacement Parallax Shader
    if (parallax && parallax.gl) {
      const glCanvas = parallax.render(image, depth, {
        panX,
        panY,
        zoom,
        focus,
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
      // Source image is wider than 9:16 -> fit height, crop width
      baseH = image.height;
      baseW = image.height * targetAspect;
    } else {
      // Source image is taller than 9:16 -> fit width, crop height
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

  // Camera choreographies designed for 2.5D depth parallax and documentary immersion
  const CAMERAS = [
    // 0: Wide establishing slow push-in with gentle vertical mist drift
    (k) => ({ zoom: lerp(1.02, 1.12, k), panX: 0.0, panY: lerp(-0.015, 0.015, k), focus: 0.35 }),
    // 1: Dramatic medium shot with lateral 3D tracking parallax (foreground shifts past background)
    (k) => ({ zoom: lerp(1.04, 1.16, k), panX: lerp(-0.025, 0.025, k), panY: lerp(-0.008, 0.008, k), focus: 0.5 }),
    // 2: Low-angle crane tilt upward with deep perspective shear
    (k) => ({ zoom: lerp(1.03, 1.15, k), panX: lerp(0.018, -0.018, k), panY: lerp(0.02, -0.02, k), focus: 0.45 }),
    // 3: Macro push-in focusing on stoic eyes / parchment writing
    (k) => ({ zoom: lerp(1.06, 1.20, k), panX: lerp(-0.012, 0.012, k), panY: lerp(0.008, -0.008, k), focus: 0.6 }),
    // 4: Expansive pull-back or epic cinematic glide
    (k) => ({ zoom: lerp(1.18, 1.04, k), panX: lerp(0.02, -0.02, k), panY: lerp(-0.015, 0.01, k), focus: 0.4 }),
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
        const cam = camFn(k);
        render25D(imgForShot, depthForShot, cam);
        drawAtmosphere(ctx, W, H, t);

        // Scene transition: soft fade from black at opening
        if (i === 0 && lt < 0.45) {
          ctx.fillStyle = `rgba(0, 0, 0, ${1 - lt / 0.45})`;
          ctx.fillRect(0, 0, W, H);
        } else if (lt < 0.12) {
          ctx.fillStyle = `rgba(0, 0, 0, ${1 - lt / 0.12})`;
          ctx.fillRect(0, 0, W, H);
        }

        // Outro fade to black in the final 1.2 seconds of video
        if (t > T.dur - 1.2) {
          const fade = clamp((t - (T.dur - 1.2)) / 1.0);
          ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
          ctx.fillRect(0, 0, W, H);
        }
      },
    });

    // Sound cues
    if (i === 0) {
      cue(0.05, 'whoosh', { gain: 0.5 });
    } else {
      cue(cut(i), 'whoosh', { gain: 0.5 });
      if (i % 2 === 1) cue(cut(i) + 0.15, 'thud', { gain: 0.6 });
      else cue(cut(i) + 0.15, 'slam', { gain: 0.5 });
    }
  }

  return { shots: S, cues: CUES };
}
