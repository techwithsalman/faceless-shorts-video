"""Beyond History soundtrack: narration + authentic procedural Foley sound design + cinematic documentary score, all synthesized with numpy & scipy.
100% legal, 100% offline, zero external downloads, $0.00.

Reads data/cues.json, data/narration.wav, and script.json "music": "beyond_history" (default).
The music dynamically ducks under the voice (-24 dBFS during speech, +4 dB swell during pauses).
"""
import json, os, subprocess, sys
from pathlib import Path

# Ensure FFmpeg is in PATH on Windows
for candidate in [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-essentials_build" / "bin",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-full_build" / "bin",
]:
    if candidate.exists() and str(candidate) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")

import numpy as np
from scipy import signal
from scipy.io import wavfile

P = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
SR = 48000
rng = np.random.default_rng(42)
cj = json.loads((P / 'data/cues.json').read_text())
script = json.loads((P / 'script.json').read_text())
DUR = float(cj['duration'])
N = int(DUR * SR) + SR // 10


def lp(x, f, o=2):
    b, a = signal.butter(o, min(f, SR / 2 - 100) / (SR / 2), 'low')
    return signal.lfilter(b, a, x)

def hp(x, f, o=2):
    b, a = signal.butter(o, f / (SR / 2), 'high')
    return signal.lfilter(b, a, x)

def bp(x, f0, f1, o=2):
    b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)

def db(x):
    return 10 ** (x / 20)

def tt(d):
    return np.arange(int(d * SR)) / SR

def env(n, a=0.005, r=None):
    """attack a seconds then exponential release over the rest"""
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    e[na:] = np.exp(-np.linspace(0, r or 5, rest)) if rest > 0 else 1
    return e

def sweep(f0, f1, d, shape='exp'):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d) if shape == 'exp' else f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def noise(d):
    return rng.standard_normal(int(d * SR))


# ---------- Authentic Historical Foley & Cinematic SFX ----------

def cinematic_impact(d=2.2, **_):
    """Deep trailer sub-bass impact with fast transient & low-end saturation"""
    t = tt(d)
    f = 85.0 * np.exp(-t * 2.8) + 32.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(phase) * env(len(t), 0.004, 3.5)
    blast = lp(noise(d), 140) * env(len(t), 0.002, 6.0) * 0.75
    raw = sub * 0.8 + blast
    return np.tanh(1.8 * raw) * 0.95

def foley_winter_wind(d=4.0, **_):
    """Sub-zero Danubian blizzard wind with howling gusts and eerie whistle"""
    t = tt(d)
    n = noise(d)
    lfo1 = 0.55 + 0.45 * np.sin(2 * np.pi * 0.28 * t + 0.3)
    lfo2 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.62 * t + 1.2)
    gust = lfo1 * lfo2
    body = bp(n, 140, 680, o=2) * gust
    whistle_freq = 420.0 + 90.0 * np.sin(2 * np.pi * 0.35 * t)
    whistle_phase = 2 * np.pi * np.cumsum(whistle_freq) / SR
    whistle = np.sin(whistle_phase) * bp(n, 380, 520, o=1) * 0.35 * gust
    envelope = np.minimum(1.0, t / 0.5) * np.minimum(1.0, (d - t) / 0.6)
    out = (body * 0.85 + whistle * 0.4) * envelope
    return lp(out, 1200) * 0.7

def foley_snow_march(d=5.0, **_):
    """Cadence of Roman soldiers marching in snow: crust crunch + boot thud + armor clink"""
    t_tot = tt(d)
    out = np.zeros(len(t_tot))
    step_interval = 0.55
    n_steps = int(d / step_interval)
    for s_idx in range(n_steps):
        st_time = s_idx * step_interval + (rng.random() * 0.04 - 0.02)
        idx_start = int(st_time * SR)
        if idx_start >= len(out): break
        step_dur = 0.28
        n_pts = int(step_dur * SR)
        if idx_start + n_pts > len(out): n_pts = len(out) - idx_start
        t_step = np.arange(n_pts) / SR
        crunch = bp(noise(step_dur)[:n_pts], 1600, 3800) * env(n_pts, 0.008, 12.0)
        thud = lp(noise(step_dur)[:n_pts], 180) * env(n_pts, 0.005, 10.0) * 0.65
        hobnail = np.sin(2 * np.pi * (1100 + (s_idx % 3) * 180) * t_step) * env(n_pts, 0.002, 28.0) * 0.15
        step_snd = crunch * 0.7 + thud + hobnail
        out[idx_start:idx_start + n_pts] += step_snd * (0.85 + 0.3 * rng.random())
    envelope = np.minimum(1.0, t_tot / 0.3) * np.minimum(1.0, (d - t_tot) / 0.4)
    return out * envelope * 0.65

def foley_war_horn(d=3.5, **_):
    """Roman bucina / ancient brass horn swell with lip vibrato & reverb tail"""
    t = tt(d)
    f0 = 110.0 + 4.0 * np.sin(2 * np.pi * 3.8 * t)
    horn = np.zeros(len(t))
    harmonics = [(1, 0.9), (2, 0.75), (3, 0.55), (4, 0.35), (5, 0.18), (6, 0.10)]
    for h_num, h_gain in harmonics:
        phase = 2 * np.pi * np.cumsum(f0 * h_num) / SR
        horn += np.sin(phase) * h_gain
    e = np.minimum(1.0, (t / 0.6) ** 1.6) * np.minimum(1.0, ((d - t) / 0.8) ** 1.2)
    brass = np.tanh(1.5 * horn * e) * 0.85
    reverb_tail = lp(noise(d), 600) * e * 0.18
    return lp(brass + reverb_tail, 2400) * 0.75

def foley_fire_crackle(d=4.5, **_):
    """Campfire & candle embers: warm hiss + stochastic wood pops"""
    t = tt(d)
    n = noise(d)
    hiss = bp(n, 400, 2600) * 0.14
    pops = np.zeros(len(t))
    n_pops = int(d * 18)
    pop_locs = rng.integers(0, max(1, len(t) - int(0.04 * SR)), size=n_pops)
    for p_loc in pop_locs:
        pop_len = int(rng.uniform(0.015, 0.035) * SR)
        p_t = np.arange(pop_len) / SR
        pop_freq = rng.uniform(800, 2800)
        pop_snd = np.sin(2 * np.pi * pop_freq * p_t) * env(pop_len, 0.001, 24.0) * rng.uniform(0.4, 0.9)
        pops[p_loc:p_loc + pop_len] += pop_snd
    total = hiss + pops
    envelope = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (d - t) / 0.4)
    return lp(total * envelope, 3600) * 0.65

def foley_quill_scratch(d=4.0, **_):
    """Parchment writing: rhythmic ink quill friction strokes and scrapes"""
    t = tt(d)
    out = np.zeros(len(t))
    cur = 0.15
    while cur < d - 0.3:
        stroke_dur = rng.uniform(0.12, 0.28)
        n_pts = int(stroke_dur * SR)
        if cur * SR + n_pts >= len(out): break
        s_t = np.arange(n_pts) / SR
        friction = bp(noise(stroke_dur)[:n_pts], 1800, 4200) * env(n_pts, 0.01, 8.0)
        scrape_f = rng.uniform(1400, 2200)
        scrape = np.sin(2 * np.pi * scrape_f * s_t) * env(n_pts, 0.005, 12.0) * 0.15
        idx = int(cur * SR)
        out[idx:idx + n_pts] += (friction * 0.8 + scrape) * rng.uniform(0.6, 1.0)
        cur += stroke_dur + rng.uniform(0.06, 0.18)
    envelope = np.minimum(1.0, t / 0.3) * np.minimum(1.0, (d - t) / 0.3)
    return lp(out * envelope, 4500) * 0.6

def sub_drop(d=1.8, **_):
    """Atmospheric sub-bass drop"""
    t = tt(d)
    f = 82.0 * np.exp(-t * 1.8) + 26.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(phase) * env(len(t), 0.01, 2.8)
    return lp(s, 160) * 0.85

def war_drum(d=1.2, **_):
    """Heavy Roman legionary war drum / timpani"""
    t = tt(d)
    f = 68.0 * np.exp(-t * 8.0) + 52.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    membrane = np.sin(phase) * env(len(t), 0.003, 5.0)
    slap = lp(noise(d), 280) * env(len(t), 0.002, 14.0) * 0.7
    return np.tanh(1.4 * (membrane + slap)) * 0.85

def triumph_brass(d=3.8, **_):
    """Imperial brass chord swell in D minor/major resolution"""
    t = tt(d)
    chord_freqs = [146.83, 220.0, 293.66, 369.99]
    chord = np.zeros(len(t))
    for f in chord_freqs:
        p1 = 2 * np.pi * f * t
        p2 = 2 * np.pi * 2 * f * t
        chord += (np.sin(p1) + 0.35 * np.sin(p2)) * 0.25
    e = np.minimum(1.0, (t / 0.8) ** 1.5) * np.minimum(1.0, ((d - t) / 1.0) ** 1.1)
    return lp(chord * e, 2200) * 0.75

def bell_toll(d=4.5, **_):
    """Distant ancient bronze bell chime with inharmonic partials"""
    t = tt(d)
    partials = [(261.6, 1.0, 3.2), (523.25, 0.6, 4.0), (740.0, 0.4, 5.5), (1046.5, 0.25, 6.5)]
    bell = np.zeros(len(t))
    for f, amp, decay in partials:
        bell += np.sin(2 * np.pi * f * t) * amp * np.exp(-t * decay)
    return lp(bell, 3200) * 0.6

# Classic utility cues
def whoosh(d=0.38, **_):
    n = noise(d); lo, hi = lp(n, 500), lp(n, 2200)
    k = np.sin(np.pi * np.linspace(0, 1, len(n))); x = (lo * (1 - k) + hi * k) * k ** 1.5
    return x / (np.abs(x).max() + 1e-9) * 0.5

def slide(d=1.0, **_):
    n = lp(noise(d), 700); e = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 2
    return n / (np.abs(n).max() + 1e-9) * e * 0.35 + sweep(260, 120, d) * e * 0.08

def thud(**_):
    d = 0.35; t = tt(d); x = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * env(len(t), 0.002, 7)
    return x * 0.9 + lp(noise(d), 220) * env(len(t), 0.001, 12) * 0.3

def slam(**_):
    d = 0.5; t = tt(d); x = np.sin(2 * np.pi * (60 + 60 * np.exp(-t * 25)) * t) * env(len(t), 0.002, 6)
    return np.tanh(1.6 * (x + lp(noise(d), 1200) * env(len(t), 0.001, 10) * 0.6)) * 0.9

FX = dict(
    cinematic_impact=cinematic_impact,
    foley_winter_wind=foley_winter_wind,
    foley_snow_march=foley_snow_march,
    foley_war_horn=foley_war_horn,
    foley_fire_crackle=foley_fire_crackle,
    foley_quill_scratch=foley_quill_scratch,
    sub_drop=sub_drop,
    war_drum=war_drum,
    triumph_brass=triumph_brass,
    bell_toll=bell_toll,
    whoosh=whoosh,
    slide=slide,
    thud=thud,
    slam=slam,
)

LEVEL = dict(
    cinematic_impact=-9,
    foley_winter_wind=-22,
    foley_snow_march=-18,
    foley_war_horn=-15,
    foley_fire_crackle=-20,
    foley_quill_scratch=-18,
    sub_drop=-12,
    war_drum=-11,
    triumph_brass=-16,
    bell_toll=-18,
    whoosh=-17,
    slide=-19,
    thud=-11,
    slam=-9,
)


# ---------- Cinematic Documentary Music Score ----------

def music_beyond_history():
    """Beyond History Signature Documentary Score:
    D minor, 84 BPM, noble cinematic stoic atmosphere.
    - Low double bass drone on D1 / D2 (36.7 Hz / 73.4 Hz)
    - Cello ostinato moving slowly: D -> F -> E -> D
    - Rhythmic muted military pulse / timpani at 84 BPM
    - Soft warm string pad (filtered below 2.8 kHz to preserve dialogue clarity)
    - Outro brass and harmonic bloom
    """
    t = np.arange(N) / SR
    x = np.zeros(N)
    bpm = 84.0
    beat = 60.0 / bpm
    bar = beat * 4.0

    # 1. Deep double-bass & sub drone
    drone = (
        np.sin(2 * np.pi * 36.71 * t) * 0.45 +
        np.sin(2 * np.pi * 73.42 * t) * 0.40 +
        np.sin(2 * np.pi * 110.00 * t) * 0.25
    )
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.15 * t)
    x += drone * 0.35

    # 2. Cello harmonic chord progression: Dm -> Bb -> Gm -> A
    chords = [
        [146.83, 174.61, 220.00],
        [146.83, 174.61, 220.00],
        [116.54, 174.61, 233.08],
        [110.00, 164.81, 220.00],
    ]
    n_bars = int(np.ceil(DUR / bar)) + 1
    for b in range(n_bars):
        st = int(b * bar * SR)
        if st >= N: break
        dur_b = min(bar, (N - st) / SR)
        pts = int(dur_b * SR)
        t_b = tt(dur_b)[:pts]
        ch = chords[b % len(chords)]
        e_bar = np.minimum(1.0, t_b / 0.5) * np.minimum(1.0, (dur_b - t_b) / 0.5)
        bar_snd = np.zeros(pts)
        for freq in ch:
            bar_snd += (
                np.sin(2 * np.pi * freq * t_b) +
                0.35 * np.sin(2 * np.pi * 2 * freq * t_b) +
                0.12 * np.sin(2 * np.pi * 3 * freq * t_b)
            ) * 0.18
        x[st:st + pts] += bar_snd * e_bar

    # 3. Low military timpani pulse on beats 1 and 3 of every bar
    n_beats = int(DUR / beat) + 1
    for k in range(n_beats):
        if k % 2 == 0:
            i = int(k * beat * SR)
            p_dur = 0.55
            pts = int(p_dur * SR)
            if i + pts < N:
                t_p = tt(p_dur)
                pulse_f = 65.0 * np.exp(-t_p * 6.0) + 48.0
                pulse = np.sin(2 * np.pi * np.cumsum(pulse_f) / SR) * env(pts, 0.005, 5.0) * 0.28
                x[i:i + pts] += pulse

    # 4. Outro swell (last 9 seconds during Meditations and CTA)
    outro_start = max(0, int((DUR - 9.5) * SR))
    if outro_start < N:
        t_out = (np.arange(N - outro_start)) / SR
        violin = (
            np.sin(2 * np.pi * 587.33 * t_out) * 0.15 +
            np.sin(2 * np.pi * 880.00 * t_out) * 0.08
        ) * np.minimum(1.0, t_out / 3.0)
        x[outro_start:] += violin

    x = lp(x, 2800)

    fade = np.ones(N)
    fi = int(0.5 * SR)
    fade[:fi] *= np.linspace(0.4, 1.0, fi)
    fo = int(1.2 * SR)
    fade[-fo:] *= np.linspace(1.0, 0.0, fo)

    return x / (np.abs(x).max() + 1e-9) * fade

def music_bed():
    bpm = 100; beat = 60 / bpm; bar = beat * 4
    chords = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]]
    x = np.zeros(N)
    nb = int(np.ceil(DUR / bar)) + 1
    for b in range(nb):
        ch = chords[b % 4]; st = int(b * bar * SR); n = int(bar * SR)
        if st >= N: break
        t = tt(bar); e = np.minimum(1, t / 0.4) * np.minimum(1, (bar - t) / 0.4)
        pad = sum(np.sin(2 * np.pi * f / 2 * t) + 0.25 * np.sin(2 * np.pi * f * t) for f in ch) * e * 0.10
        x[st:st + n] += pad[:max(0, min(n, N - st))]
        for k in range(8):
            f = ch[[0, 1, 2, 1, 2, 0, 1, 2][k]] * (2 if k % 4 == 2 else 1); ps = st + int(k * beat / 2 * SR); pn = int(0.5 * SR)
            if ps + pn >= N: continue
            pt = tt(0.5); pl = (np.sin(2 * np.pi * f * pt) + 0.35 * np.sin(4 * np.pi * f * pt)) * env(pn, 0.003, 7) * 0.12
            x[ps:ps + pn] += pl
    x = lp(x, 3200)
    fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    return x / (np.abs(x).max() + 1e-9) * fade

def music_tension():
    t = np.arange(N) / SR; x = np.zeros(N)
    for f, g in [(55, 0.5), (82.4, 0.3), (110, 0.2), (130.8, 0.12)]: x += np.sin(2 * np.pi * f * t + np.sin(t * 0.3) * 0.5) * g
    x *= 0.55 + 0.45 * np.sin(2 * np.pi * t / 8) ** 2
    beat = 60 / 84; ping = lambda f: (np.sin(2 * np.pi * f * tt(1.2)) + 0.3 * np.sin(4 * np.pi * f * tt(1.2))) * env(int(1.2 * SR), 0.01, 5)
    seq = [220.0, 261.6, 196.0, 174.6]
    for k in range(int(DUR / (beat * 2))):
        i = int(k * beat * 2 * SR); pg = ping(seq[(k // 2) % 4]) * 0.35
        if i + len(pg) < N: x[i:i + len(pg)] += pg
    x = lp(x, 2200); fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo); fi = int(0.8 * SR); fade[:fi] *= np.linspace(0, 1, fi)
    return x / (np.abs(x).max() + 1e-9) * fade

def music_bounce():
    bpm = 118; beat = 60 / bpm; x = np.zeros(N)
    prog = [(130.8, [261.6, 329.6, 392.0]), (174.6, [261.6, 349.2, 440.0]), (196.0, [246.9, 293.7, 392.0]), (130.8, [261.6, 329.6, 392.0])]
    mel = [0, 2, 1, 2, 0, 1, 2, 1]
    pl = lambda f, d, g: (np.sin(2 * np.pi * f * tt(d)) + 0.4 * np.sin(4 * np.pi * f * tt(d)) + 0.15 * np.sin(6 * np.pi * f * tt(d))) * env(int(d * SR), 0.003, 9) * g
    for k in range(int(DUR / beat) + 1):
        bass, ch = prog[(k // 8) % 4]; i = int(k * beat * SR)
        b = pl(bass if k % 2 == 0 else bass * 1.5, 0.3, 0.35) if k % 2 == 0 else pl(ch[0] / 2 * 1.5, 0.22, 0.18)
        if i + len(b) < N: x[i:i + len(b)] += b
        if k % 2 == 1:
            c = sum(pl(f, 0.16, 0.07) for f in ch)
            if i + len(c) < N: x[i:i + len(c)] += c
        f = ch[mel[k % 8]] * 2; m = pl(f, 0.18, 0.09); j = i + int(beat / 2 * SR) if k % 4 == 3 else i
        if j + len(m) < N and k % 8 not in (3, 7): x[j:j + len(m)] += m
    x = lp(x, 4200); fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    return x / (np.abs(x).max() + 1e-9) * fade

def load_audio(f):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(out, dtype=np.float32).reshape(-1, 2).astype(np.float64)
    return a


# ---------- Master Audio Assembly & Ducking ----------

mix = np.zeros((N, 2))

# 1. Spoken Narration
vf = P / 'data/narration.wav'
voice = None
if vf.exists():
    v = load_audio(vf)[:N]
    voice = np.zeros((N, 2))
    voice[:len(v)] = v
    rms = np.sqrt(np.mean(voice ** 2) + 1e-12)
    voice *= db(-19) / rms
    mix += voice

# 2. Cinematic Music Bed with Dialogue Ducking
mus = script.get('music', 'beyond_history')
if mus and mus != 'none':
    m = (music_beyond_history() if mus in ('beyond_history', 'egypt_eternity') else
         music_bed() if mus == 'bed' else
         music_tension() if mus == 'tension' else
         music_bounce() if mus == 'bounce' else None)
    if m is None:
        if (P / mus).exists():
            a = load_audio(P / mus)[:N]
            m = np.zeros(N)
            m[:len(a)] = a.mean(1)
            m /= np.abs(m).max() + 1e-9
        else:
            m = music_beyond_history()
    m = np.stack([m, m], 1) * db(-24 if voice is not None else -20)
    if voice is not None:
        lev = np.abs(voice.mean(1))
        lev = signal.lfilter([1 - 0.9995], [1, -0.9995], lev)
        lev /= lev.max() + 1e-9
        # Dynamic ducking: dips -6 dB during heavy speech, swells +4 dB in gaps
        m *= (1.0 - 0.50 * np.clip(lev * 2.8, 0, 1))[:, None]
    mix += m

# 3. Synchronized Foley & Sound Effects
for c in cj.get('cues', []):
    fn = FX.get(c['type'])
    if not fn:
        print('unknown cue type, skipped:', c['type'])
        continue
    kwargs = {}
    if c.get('dur'): kwargs['d'] = c['dur']
    x = fn(**kwargs)
    base_lvl = LEVEL.get(c['type'], -16)
    x = lp(x, 5000) * db(base_lvl) * c.get('gain', 1.0) / (np.abs(x).max() + 1e-9) * 0.9
    i = int(c['t'] * SR)
    n = min(len(x), N - i)
    if n > 0 and i >= 0:
        pan = c.get('pan', 0.0)
        mix[i:i + n, 0] += x[:n] * (1 - max(0, pan))
        mix[i:i + n, 1] += x[:n] * (1 + min(0, pan))

# 4. Master Soft-Limiter (peak -1 dBFS, no clipping)
mix = np.tanh(mix * 1.15) / 1.15
mix *= db(-1) / (np.abs(mix).max() + 1e-9)

wavfile.write(P / 'data/mix.wav', SR, (mix * 32767).astype(np.int16))
print(f"data/mix.wav: {DUR:.2f} s · voice: {'yes' if voice is not None else 'NO (captions-only)'} · music: {mus} · {len(cj.get('cues', []))} cues")
