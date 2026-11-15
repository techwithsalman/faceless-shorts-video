// THE MAN WHO BOUGHT A BANK FOR $1: the shot list (Tall Tale 3D).
// A shot: { id, at, note, draw(lt, d, t, blit) }: pose cut-out people, move camera, E.render(...), blit(),
// then 2D overlay. Every shot moves the camera.
import * as THREE from 'three';
import { ctx, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import * as WD from './core/world.js';
import * as PR from './core/props.js';
import { Toon, PROPS } from './core/toon.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const mix = (a, b, k) => a.clone().lerp(b, k);
const talk = (t, on = 1) => (on ? 0.25 + 0.75 * Math.abs(Math.sin(t * 13)) * (0.6 + 0.4 * Math.sin(t * 5.3)) : 0);
const blink = (t, off = 0) => (((t + off) % 3.3) < 0.12 ? 1 : 0);

// the cast
const LOOK = {
  buyer: { body: '#2A3045', hat: 'tophat', hatCol: '#1E2233', neck: 'bowtie', neckCol: '#D8343F', pattern: 'vest', patCol: '#1E2233', extra: ['mustache', 'monocle'] },
  banker: { body: '#3E5FA8', hat: 'bowler', hatCol: '#2E4E8A', neck: 'tie', neckCol: '#E2B33C', extra: ['glasses'] },
  trader: { body: '#E8634A', pattern: 'plain', neck: 'tie', neckCol: '#3C6FB6', extra: ['freckles'] },
  regulator: { body: '#4A4560', hat: 'bowler', hatCol: '#2A2638', neck: 'collar', pattern: 'vest', patCol: '#2A2638', extra: ['mustache'] },
  citizen: { body: '#6FA35A', hat: 'cap', hatCol: '#3E6F38', neck: 'none', pattern: 'plain' },
};
const person = (k, opts) => new Toon({ ...LOOK[k], extra: [...(LOOK[k].extra || [])] }, opts);

export function buildShots(E) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.06);
  const cam = camera(36);
  const LOOKS = {
    street: { bloom: 0.18, aperture: 0.0012, maxblur: 0.008 },
    room: { bloom: 0.28, aperture: 0.001, maxblur: 0.008 },
    dusk: { bloom: 0.22, aperture: 0.0015, maxblur: 0.009, exposure: 0.85, warm: 0.06 },
  };

  const shoot = (scene, people, from, to, at, at2, k, look, focus) => {
    if (cam.fov !== (look.fov || 36)) { cam.fov = look.fov || 36; cam.updateProjectionMatrix(); }
    cam.position.copy(mix(from, to, k)); cam.lookAt(at2 ? mix(at, at2, k) : at);
    people.forEach((p) => p.face(cam));
    E.render(scene, cam, { ...look, focus: focus ?? cam.position.distanceTo(at2 ? mix(at, at2, k) : at) });
  };

  // ── SET 1: Main Street with Bank Facade ─────────────────────────────────────
  const SHOP_ORDER = [
    ['GRAND HOTEL', '#9E4A3A', 'brick', null],
    ['BARBER', '#E3C16F', 'wood', '#3C6FB6'],
    ['BANK', '#C7B79A', 'brick', null],
    ['POST OFFICE', '#7FA36A', 'wood', '#2E4E8A'],
    ['CAFE', '#E58A6A', 'wood', '#2E4E3F'],
    ['BAKERY', '#C9603F', 'brick', '#D8343F'],
  ];
  const ST = WD.mainStreet(E, { shops: SHOP_ORDER, len: 50 });
  ST.sun.key.target.position.set(-4, 0, 0); ST.sun.key.position.set(5, 13, 6);
  const bankBldg = ST.buildings.find((b) => b.name === 'BANK') || { z: -15, x: -6.2 };
  const bz = bankBldg.z;

  const stBuyer = person('buyer');
  const stCitizen = person('citizen');
  [stBuyer, stCitizen].forEach((p) => ST.scene.add(p.group));
  const stPeople = [...ST.people, stBuyer, stCitizen];

  // ── SET 2: Barings Bank Grand Interior ─────────────────────────────────────
  const viewTex = () => {
    const c = new THREE.PerspectiveCamera(40, 4 / 3, 0.1, 500);
    c.position.set(0, 1.8, -10); c.lookAt(-5, 2, bz);
    return WD.snapshot(E, ST.scene, c);
  };
  const BANK_IN = WD.interior(E, {
    w: 8, depth: 7, h: 4.2, wall: '#1F3B2E', motif: '#2E5442', floor: '#A8693E', ceiling: '#3A281E',
    signText: 'BARINGS BANK · EST 1762', picture: false, view: viewTex(),
  });
  const inBanker = person('banker'); inBanker.at(3.55, 0, -2.5); BANK_IN.scene.add(inBanker.group);
  const inDesk = PR.desk(2.4); inDesk.position.set(0.5, 0, -3.2); BANK_IN.scene.add(inDesk);
  const cub = PR.cubbies(2.6, 2.2); cub.position.set(-2.4, 0.95, -6.75); BANK_IN.scene.add(cub);
  const moneyPiles = [];
  for (let i = 0; i < 4; i++) {
    const p = PR.parcel(0.5, 0.35, 0.4); p.position.set(-2.8 + i * 0.5, 0.18, -4.5 + (i % 2) * 0.4);
    BANK_IN.scene.add(p); moneyPiles.push(p);
  }
  const inPeople = [inBanker];

  // ── SET 3: Singapore Trading Desk ──────────────────────────────────────────
  const TRADING = WD.interior(E, {
    w: 7, depth: 6, h: 4.0, wall: '#27384E', motif: '#364B66', floor: '#6E422C', ceiling: '#1C2636',
    signText: 'SIMEX TRADING FLOOR', counterOn: false, picture: false,
  });
  const trDesk = PR.desk(2.6); trDesk.position.set(0, 0, -3.0); TRADING.scene.add(trDesk);
  const trader = person('trader'); trader.at(0, 0, -3.85); TRADING.scene.add(trader.group);
  const tradingPeople = [trader];

  // ── SET 4: Bank of England Emergency War Room ──────────────────────────────
  const WAR_ROOM = WD.interior(E, {
    w: 8, depth: 7, h: 4.2, wall: '#4A2A2A', motif: '#5E3434', floor: '#7A4830', ceiling: '#261818',
    signText: 'BANK OF ENGLAND · EMERGENCY', counterOn: false, picture: false,
  });
  const warDesk = PR.desk(2.8); warDesk.position.set(0.2, 0, -3.2); WAR_ROOM.scene.add(warDesk);
  const warReg = person('regulator'); warReg.at(-1.4, 0, -3.2); WAR_ROOM.scene.add(warReg.group);
  const warBuyer = person('buyer'); warBuyer.at(1.8, 0, -3.2); WAR_ROOM.scene.add(warBuyer.group);
  const warPeople = [warReg, warBuyer];

  // ══════════════════════════════ SHOTS ══════════════════════════════

  // ── S01 · HOOK (0.00 - 5.17): "In 1995, a man bought an entire two-hundred-year-old bank"
  add({
    id: 'S01', at: cut(0), note: 'Crane down main street to the Bank; the buyer stands proudly',
    draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      stBuyer.at(-5.0, 0.18, bz + 0.8);
      stBuyer.set({ mood: 'smug', armR: [45, 70], holdR: PROPS.bill, lean: 3, blink: blink(t) });
      stCitizen.at(-4.8, 0.18, bz - 2.5);
      stCitizen.set({ mood: 'neutral', legs: 'walk', phase: t * 5 });
      shoot(ST.scene, stPeople, V3(0.5, 6.2, bz - 16), V3(-2.2, 1.8, bz - 3.5), V3(-3.5, 3.2, bz), V3(-4.8, 1.3, bz + 0.8), k, { ...LOOKS.street, fov: 42 });
      blit();
    },
  });
  cue(0.05, 'whoosh', { gain: 0.6 });
  cue(Wd('bought', 0), 'ding', { gain: 0.7 });

  // ── S02 · REVEAL (5.17 - 6.81): "for exactly one dollar."
  add({
    id: 'S02', at: cut(1), note: 'Punch-in close-up on the buyer holding the $1 bill with gold stamp',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      stBuyer.at(-5.0, 0.18, bz + 0.8);
      stBuyer.set({ mood: 'smug', armR: [55, 85], holdR: PROPS.bill, armL: [25, 20], lean: 2, blink: blink(t) });
      shoot(ST.scene, [stBuyer], V3(-3.2, 1.6, bz - 0.2), V3(-3.5, 1.55, bz + 0.2), V3(-5.0, 1.45, bz + 0.8), null, k, { ...LOOKS.street, fov: 32 });
      blit();

      // 2D Stamp Overlay: "$1.00"
      const p = clamp((lt - 0.1) / 0.35);
      if (p > 0) {
        ctx.save();
        ctx.translate(540, 520);
        const sc = lerp(2.2, 1.0, eob(p));
        ctx.scale(sc, sc);
        ctx.rotate(-0.08);
        ctx.fillStyle = 'rgba(230, 185, 60, 0.95)';
        ctx.strokeStyle = '#1F1C33';
        ctx.lineWidth = 12;
        ctx.beginPath();
        ctx.roundRect(-220, -75, 440, 150, 24);
        ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#1F1C33';
        ctx.font = '900 82px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('$1.00', 0, 4);
        ctx.restore();
      }
    },
  });
  cue(cut(1), 'pop', { gain: 0.8 });
  cue(cut(1) + 0.15, 'stamp', { gain: 0.9 });

  // ── S03 · ROYAL BANK (6.81 - 9.84): "Barings was Queen Elizabeth's personal bank,"
  add({
    id: 'S03', at: cut(2), note: 'Inside Barings Bank: stately banker with the royal ledger book',
    draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      inBanker.set({ mood: 'proud', armL: [35, 45], holdL: PROPS.book('ROYAL', 1), armR: [20, 10], blink: blink(t), talk: talk(t) });
      shoot(BANK_IN.scene, inPeople, V3(0.2, 1.9, 1.5), V3(0.8, 1.85, 0.4), V3(3.55, 1.8, -2.5), null, k, LOOKS.room);
      blit();
    },
  });
  cue(cut(2), 'whoosh', { gain: 0.5 });
  cue(Wd('Elizabeth', 2), 'sparkle', { gain: 0.7 });

  // ── S04 · WORLD EMPIRES (9.84 - 12.61): "and had funded world empires for centuries."
  add({
    id: 'S04', at: cut(3), note: 'Bank vault view: stacks of wealth and prestigious history',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      inBanker.at(1.5, 0, -3.2);
      inBanker.set({ mood: 'happy', armR: [65, -40], holdR: PROPS.stack, blink: blink(t) });
      shoot(BANK_IN.scene, inPeople, V3(-1.6, 1.6, -1.0), V3(-1.1, 1.55, -1.8), V3(1.2, 1.4, -3.4), null, k, LOOKS.room);
      blit();
    },
  });
  cue(cut(3), 'slide', { gain: 0.5 });
  cue(Wd('empires', 3), 'ding', { gain: 0.6 });

  // ── S05 · THE TRADER (12.61 - 15.85): "Until a twenty-eight-year-old trader in Singapore"
  add({
    id: 'S05', at: cut(4), note: 'Singapore SIMEX trading desk: young trader at desk with papers',
    draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      trader.set({ legs: 'sit', mood: 'sly', armL: [45, 60], holdL: PROPS.paper('NIKKEI'), armR: [40, 70], blink: blink(t), talk: talk(t) });
      shoot(TRADING.scene, tradingPeople, V3(-0.3, 1.9, -0.6), V3(0.1, 1.85, -1.2), V3(0, 1.4, -3.5), null, k, LOOKS.room);
      blit();
    },
  });
  cue(cut(4), 'whoosh', { gain: 0.6 });

  // ── S06 · THE GAMBLE (15.85 - 19.09): "secretly gambled on the Japanese stock market,"
  add({
    id: 'S06', at: cut(5), note: 'Close-up on trader sweating as charts plunge downward',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      trader.set({ legs: 'sit', mood: 'worried', armL: [60, 40], holdL: PROPS.paper('NIKKEI -800'), sweat: 1, blink: blink(t) });
      shoot(TRADING.scene, tradingPeople, V3(-0.2, 1.6, -2.0), V3(0.0, 1.55, -2.4), V3(0, 1.4, -3.8), null, k, { ...LOOKS.room, fov: 32 });
      blit();
    },
  });
  cue(cut(5), 'tock', { gain: 0.7 });

  // ── S07 · A BILLION DOLLARS (19.09 - 21.36): "and lost over a billion dollars."
  add({
    id: 'S07', at: cut(6), note: 'Full panic! Red flash and giant loss figure',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      trader.set({ legs: 'sit', mood: 'shock', armL: [110, -50], armR: [110, 50], sweat: 2, squash: -0.15, blink: 0 });
      shoot(TRADING.scene, tradingPeople, V3(0.1, 1.55, -2.6), V3(0.0, 1.5, -2.9), V3(0, 1.35, -3.8), null, k, { ...LOOKS.room, fov: 30 });
      blit();

      // Red Alert Flash & Stamp: "-$1.4 BILLION"
      const p = clamp(lt / 0.3);
      ctx.save();
      ctx.translate(540, 560);
      const sc = lerp(2.4, 1.0, eob(p));
      ctx.scale(sc, sc);
      ctx.fillStyle = 'rgba(216, 52, 63, 0.95)';
      ctx.strokeStyle = '#1F1C33';
      ctx.lineWidth = 14;
      ctx.beginPath();
      ctx.roundRect(-300, -85, 600, 170, 28);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '900 70px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('-$1.4 BILLION', 0, 4);
      ctx.restore();
    },
  });
  cue(cut(6), 'alarm', { gain: 0.8 });
  cue(Wd('billion', 6), 'thud', { gain: 0.9 });

  // ── S08 · COLLAPSE OVERNIGHT (21.36 - 24.01): "The oldest bank in Britain collapsed overnight."
  add({
    id: 'S08', at: cut(7), note: 'Dusk exterior: Bank doors closed, shocked citizens outside',
    draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      stCitizen.at(-4.8, 0.18, bz);
      stCitizen.set({ mood: 'shock', armL: [80, 20], armR: [80, -20], sweat: 1 });
      shoot(ST.scene, [stCitizen], V3(-2.2, 1.8, bz - 5.0), V3(-2.8, 1.7, bz - 3.2), V3(-5.0, 1.6, bz), null, k, LOOKS.dusk);
      blit();

      // Closed sign
      ctx.save();
      ctx.translate(540, 440);
      ctx.rotate(0.04);
      ctx.fillStyle = '#D8343F';
      ctx.strokeStyle = '#1F1C33';
      ctx.lineWidth = 10;
      ctx.fillRect(-180, -50, 360, 100);
      ctx.strokeRect(-180, -50, 360, 100);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '900 52px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('CLOSED', 0, 0);
      ctx.restore();
    },
  });
  cue(cut(7), 'slam', { gain: 0.8 });

  // ── S09 · PANICKED REGULATORS (24.01 - 26.75): "Panicked regulators scrambled for a buyer,"
  add({
    id: 'S09', at: cut(8), note: 'Bank of England war room: regulator pacing in panic',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      warReg.at(-1.4, 0, -3.2);
      warReg.set({ mood: 'worried', legs: 'walk', phase: t * 7, armL: [60, -30], armR: [60, 30], sweat: 1 });
      warBuyer.group.visible = false;
      shoot(WAR_ROOM.scene, [warReg], V3(0.8, 1.9, -0.8), V3(0.4, 1.85, -1.6), V3(-1.2, 1.5, -3.2), null, k, LOOKS.room);
      blit();
    },
  });
  cue(cut(8), 'whoosh', { gain: 0.5 });
  cue(cut(8) + 0.4, 'tock', { gain: 0.6 });

  // ── S10 · THE DUTCH BANKER (26.75 - 29.84): "until a Dutch banker offered to take everything,"
  add({
    id: 'S10', at: cut(9), note: 'The Dutch buyer walks into the meeting room calm and confident',
    draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      warBuyer.group.visible = true;
      warBuyer.at(lerp(2.6, 1.2, k), 0, -3.2);
      warBuyer.set({ mood: 'smug', legs: 'walk', phase: t * 5, armR: [45, 60], holdR: PROPS.bill, blink: blink(t) });
      warReg.set({ mood: 'shock', armL: [30, -20], sweat: 1 });
      shoot(WAR_ROOM.scene, warPeople, V3(-0.6, 1.9, -0.6), V3(-0.2, 1.85, -1.2), V3(1.2, 1.5, -3.2), null, k, LOOKS.room);
      blit();
    },
  });
  cue(cut(9), 'whoosh', { gain: 0.6 });
  cue(Wd('offered', 9), 'ding', { gain: 0.7 });

  // ── S11 · CHOCOLATE BAR (29.84 - 32.58): "for the price of a single chocolate bar."
  add({
    id: 'S11', at: cut(10), note: 'Close-up on desk: single $1 bill placed on the acquisition contract',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      warBuyer.at(0.9, 0, -3.2);
      warBuyer.set({ mood: 'smug', armR: [55, 75], holdR: PROPS.bill, blink: blink(t) });
      warReg.at(-0.9, 0, -3.2);
      warReg.set({ mood: 'shock', armL: [70, 40], sweat: 1 });
      shoot(WAR_ROOM.scene, warPeople, V3(0.0, 1.55, -1.6), V3(0.0, 1.5, -1.9), V3(0.0, 1.15, -3.1), null, k, { ...LOOKS.room, fov: 30 });
      blit();
    },
  });
  cue(cut(10), 'pop', { gain: 0.7 });
  cue(Wd('chocolate', 10), 'ding', { gain: 0.8 });

  // ── S12 · OWNING THE ROYAL BANK (32.58 - 34.63): "He walked away owning the royal bank"
  add({
    id: 'S12', at: cut(11), note: 'Buyer walks out of the bank with keys in bright sunlight',
    draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      stBuyer.at(-5.0, 0.18, bz + lerp(-1.0, 2.0, k));
      stBuyer.set({ mood: 'laugh', legs: 'walk', phase: t * 6, armR: [50, 40], holdR: PROPS.key, blink: blink(t) });
      shoot(ST.scene, [stBuyer], V3(-2.8, 1.8, bz + 4.5), V3(-3.2, 1.75, bz + 3.2), V3(-5.0, 1.45, bz + 0.5), null, k, LOOKS.street);
      blit();
    },
  });
  cue(cut(11), 'whoosh', { gain: 0.6 });
  cue(Wd('royal', 11), 'ding', { gain: 0.8 });

  // ── S13 · THE $1 BUCK (34.63 - 37.60): "for just one single buck."
  add({
    id: 'S13', at: cut(12), note: 'Final heroic pose with $1 bill and golden victory banner',
    draw(lt, d, t, blit) {
      const k = eo(clamp(lt / d));
      stBuyer.at(-5.0, 0.18, bz + 2.0);
      stBuyer.set({ mood: 'smug', armR: [60, 80], holdR: PROPS.bill, armL: [30, 20], lean: 2, blink: blink(t) });
      shoot(ST.scene, [stBuyer], V3(-3.4, 1.6, bz + 1.2), V3(-3.6, 1.55, bz + 1.5), V3(-5.0, 1.4, bz + 2.0), null, k, { ...LOOKS.street, fov: 32 });
      blit();

      // Victory Banner: "BOUGHT FOR $1.00"
      const p = clamp(lt / 0.4);
      ctx.save();
      ctx.translate(540, 500);
      const sc = lerp(2.2, 1.0, eob(p));
      ctx.scale(sc, sc);
      ctx.rotate(-0.04);
      ctx.fillStyle = '#E9C75A';
      ctx.strokeStyle = '#1F1C33';
      ctx.lineWidth = 14;
      ctx.beginPath();
      ctx.roundRect(-270, -80, 540, 160, 26);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#1F1C33';
      ctx.font = '900 64px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('BOUGHT FOR $1', 0, 4);
      ctx.restore();
    },
  });
  cue(cut(12), 'ding', { gain: 0.9 });
  cue(cut(12) + 0.4, 'sparkle', { gain: 0.8 });

  return { shots: S, cues: CUES };
}
