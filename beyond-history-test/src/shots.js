// Beyond History: 3-Scene Cinematic Historical Documentary Test
import { ctx, W, H, clamp, lerp, eio, eo } from './core/lib.js';
import { L, Wd } from './core/timing.js';
import { drawAtmosphere } from './core/atmosphere.js';

export function buildShots(img) {
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.04);

  // Helper to render high-res image with smooth cinematic 2.5D camera (pan, zoom, tilt)
  function render25D(image, { zoom = 1.0, panX = 0, panY = 0, focusX = 0.5, focusY = 0.5 }) {
    ctx.save();
    ctx.fillStyle = '#0B0B0E';
    ctx.fillRect(0, 0, W, H);

    // Calculate source rect
    const srcW = image.width / zoom;
    const srcH = image.height / zoom;
    const centerX = image.width * focusX + panX;
    const centerY = image.height * focusY + panY;
    const sx = clamp(centerX - srcW / 2, 0, image.width - srcW);
    const sy = clamp(centerY - srcH / 2, 0, image.height - srcH);

    ctx.drawImage(image, sx, sy, srcW, srcH, 0, 0, W, H);
    ctx.restore();
  }

  // ── Shot 1 (0.00 – 2.62 s): Establishing Shot — The Frontier Command Tent ──
  add({
    id: 'S01',
    at: cut(0),
    note: 'Wide establishing push-in: Marcus Aurelius in his tent by candlelight',
    draw(lt, d, t) {
      const k = eio(clamp(lt / d));
      const zoom = lerp(1.0, 1.14, k);
      const panY = lerp(0, -30, k);

      render25D(img, { zoom, panY, focusX: 0.51, focusY: 0.52 });
      drawAtmosphere(ctx, W, H, t);

      // Scene transition: soft fade from black at the very start
      if (lt < 0.45) {
        ctx.fillStyle = `rgba(0, 0, 0, ${1 - lt / 0.45})`;
        ctx.fillRect(0, 0, W, H);
      }
    },
  });
  cue(0.05, 'whoosh', { gain: 0.5 });
  cue(Wd('Germania', 0), 'sparkle', { gain: 0.6 });

  // ── Shot 2 (2.62 – 6.85 s): Medium Close-Up — Weathered Stoic Commander ────
  add({
    id: 'S02',
    at: cut(1),
    note: 'Dramatic close-up: Marcus Aurelius weathered stoic face and armor',
    draw(lt, d, t) {
      const k = eo(clamp(lt / d));
      const zoom = lerp(1.68, 1.84, k);
      const panX = lerp(-25, 20, k);
      const panY = lerp(-10, 15, k);

      render25D(img, { zoom, panX, panY, focusX: 0.52, focusY: 0.42 });
      drawAtmosphere(ctx, W, H, t);

      // Subtle flash cut on transition
      if (lt < 0.12) {
        ctx.fillStyle = `rgba(0, 0, 0, ${1 - lt / 0.12})`;
        ctx.fillRect(0, 0, W, H);
      }
    },
  });
  cue(cut(1), 'whoosh', { gain: 0.6 });
  cue(Wd('twelve', 1), 'thud', { gain: 0.8 });
  cue(Wd('war', 1), 'slam', { gain: 0.7 });

  // ── Shot 3 (6.85 – 12.81 s): Macro Tilt — Philosophical Resolve & Meditations
  add({
    id: 'S03',
    at: cut(2),
    note: 'Upward crane tilt: from imperial bronze armor and scrolls to stoic eyes',
    draw(lt, d, t) {
      const k = eio(clamp(lt / d));
      const zoom = lerp(1.42, 1.58, k);
      const focusY = lerp(0.58, 0.43, k);
      const panX = lerp(15, -10, k);

      render25D(img, { zoom, panX, focusX: 0.50, focusY });
      drawAtmosphere(ctx, W, H, t);

      // Transition cut
      if (lt < 0.14) {
        ctx.fillStyle = `rgba(0, 0, 0, ${1 - lt / 0.14})`;
        ctx.fillRect(0, 0, W, H);
      }

      // Elegant outro fade to black
      if (t > 11.5) {
        const fade = clamp((t - 11.5) / 1.1);
        ctx.fillStyle = `rgba(0, 0, 0, ${fade})`;
        ctx.fillRect(0, 0, W, H);
      }
    },
  });
  cue(cut(2), 'whoosh', { gain: 0.5 });
  cue(Wd('Rome', 2), 'sparkle', { gain: 0.7 });
  cue(Wd('mind', 3), 'ding', { gain: 0.8 });

  return { shots: S, cues: CUES };
}
