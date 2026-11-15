// Professional documentary subtitles: elegant serif typography, gold active word highlight
import { ctx, W, H, clamp } from './lib.js';
import { T } from './timing.js';

let CAPTIONS = [];

export function buildCaptions(script) {
  const words = T.words || [];
  CAPTIONS = [];

  // Group words into natural documentary subtitle chunks (2-4 words)
  let chunk = [];
  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    chunk.push(w);
    const isPunct = /[.,:;?!]$/.test(w.w);
    const isLong = chunk.length >= 3;
    const isLast = i === words.length - 1;
    const nextLine = !isLast && words[i + 1].line !== w.line;

    if (isPunct || isLong || nextLine || isLast) {
      const s = chunk[0].s;
      const e = chunk[chunk.length - 1].e + 0.15;
      CAPTIONS.push({
        s,
        e,
        words: chunk.map((tok) => ({
          txt: tok.w,
          s: tok.s,
          e: tok.e,
        })),
      });
      chunk = [];
    }
  }
}

export function drawCaption(t) {
  const cap = CAPTIONS.find((c) => t >= c.s && t <= c.e);
  if (!cap) return;

  ctx.save();
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '700 52px Caladea, Georgia, serif';
  ctx.letterSpacing = '1px';

  const fullText = cap.words.map((w) => w.txt).join(' ');
  const textWidth = ctx.measureText(fullText).width;

  const y = 1560; // Cinematic lower-third zone

  // Soft subtle dark backing gradient for readability
  const bg = ctx.createLinearGradient(0, y - 55, 0, y + 55);
  bg.addColorStop(0, 'rgba(0, 0, 0, 0.0)');
  bg.addColorStop(0.5, 'rgba(10, 10, 14, 0.72)');
  bg.addColorStop(1, 'rgba(0, 0, 0, 0.0)');
  ctx.fillStyle = bg;
  ctx.fillRect(W / 2 - textWidth / 2 - 40, y - 50, textWidth + 80, 100);

  // Render words: highlight current active word in gold
  const startX = W / 2 - textWidth / 2;
  let curX = startX;

  for (const w of cap.words) {
    const isActive = t >= w.s && t <= w.e + 0.08;
    const wStr = w.txt + ' ';
    const wW = ctx.measureText(wStr).width;

    ctx.save();
    // Shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.95)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 3;

    if (isActive) {
      ctx.fillStyle = '#F5D061'; // Imperial Gold
      ctx.fillText(wStr, curX + wW / 2, y);
    } else {
      ctx.fillStyle = '#FFF9EE'; // Warm Classical Ivory
      ctx.fillText(wStr, curX + wW / 2, y);
    }
    ctx.restore();

    curX += wW;
  }

  ctx.restore();
}

export function captionList() {
  return CAPTIONS;
}
