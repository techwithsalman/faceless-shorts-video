// Beyond History Cinematic Engine Boot
import { W, H, setCtx, ctx, clamp } from './core/lib.js';
import { T, loadTiming } from './core/timing.js';
import { buildCaptions, drawCaption, captionList } from './core/captions.js';
import { buildShots } from './shots.js';

const cv = document.getElementById('cv');
setCtx(cv.getContext('2d'));
const OP = (window.OP = { ready: false });

function draw(t) {
  t = clamp(t, 0, T.dur - 1e-4);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;

  const S = OP._shots;
  let i = S.length - 1;
  while (i > 0 && S[i].at > t) i--;
  const sh = S[i];
  const end = i < S.length - 1 ? S[i + 1].at : T.dur;
  const d = end - sh.at;
  const lt = t - sh.at;

  ctx.save();
  sh.draw(lt, d, t);
  ctx.restore();

  // Draw synchronized documentary subtitles
  drawCaption(t);
}

(async () => {
  try {
    await document.fonts.load('700 60px Caladea');
    await document.fonts.load('900 60px Inter');

    const script = await (await fetch('script.json', { cache: 'no-store' })).json();
    await loadTiming();
    buildCaptions(script);

    // Load master photorealistic scene image
    const img = new Image();
    img.src = 'assets/marcus_aurelius.jpg';
    await new Promise((res, rej) => {
      img.onload = res;
      img.onerror = rej;
    });

    const { shots, cues } = buildShots(img);
    shots.sort((a, b) => a.at - b.at);

    OP._shots = shots;
    OP.script = script;
    OP.duration = () => T.dur;
    OP.draw = draw;
    OP.frame = (t, q = 0.94) => {
      draw(t);
      return cv.toDataURL('image/jpeg', q);
    };
    OP.shots = () =>
      shots.map((s, idx) => ({
        id: s.id,
        at: +s.at.toFixed(3),
        end: +(idx < shots.length - 1 ? shots[idx + 1].at : T.dur).toFixed(3),
        note: s.note || '',
      }));
    OP.captions = () =>
      captionList().map((c) => ({
        s: +c.s.toFixed(3),
        e: +c.e.toFixed(3),
        text: c.words.map((w) => w.txt).join(' '),
      }));
    OP.cues = () => cues.slice().sort((a, b) => a.t - b.t);
    OP.ready = true;

    const q = new URLSearchParams(location.search);
    if (!q.has('capture')) {
      if (q.has('t')) draw(+q.get('t'));
      else {
        const audio = new Audio('data/mix.wav');
        let t0 = null;
        const btn = document.getElementById('play');
        btn.hidden = false;
        btn.onclick = () => {
          btn.hidden = true;
          t0 = performance.now();
          audio.currentTime = 0;
          audio.play().catch(() => {});
          const tick = () => {
            const cur = (performance.now() - t0) / 1000;
            if (cur < T.dur) {
              draw(cur);
              requestAnimationFrame(tick);
            }
          };
          requestAnimationFrame(tick);
        };
      }
    }
  } catch (e) {
    OP.bootError = e.message;
    console.error(e);
  }
})();
