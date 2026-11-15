"""Beyond History: The Library of Alexandria Documentary Soundtrack Engine
100% Free, Offline, Local Procedural Audio via numpy & scipy ($0.00, No Copyright).
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
rng = np.random.default_rng(101)
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
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    e[na:] = np.exp(-np.linspace(0, r or 5, rest)) if rest > 0 else 1
    return e

def noise(d):
    return rng.standard_normal(int(d * SR))


# ---------- Foley Effects Tailored for Alexandria ----------

def cinematic_impact(d=2.2, **_):
    t = tt(d)
    f = 85.0 * np.exp(-t * 2.8) + 32.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(phase) * env(len(t), 0.004, 3.5)
    blast = lp(noise(d), 140) * env(len(t), 0.002, 6.0) * 0.75
    raw = sub * 0.8 + blast
    return np.tanh(1.8 * raw) * 0.95

def sub_drop(d=1.8, **_):
    t = tt(d)
    f = 82.0 * np.exp(-t * 1.8) + 26.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(phase) * env(len(t), 0.01, 2.8)
    return lp(s, 160) * 0.85

def foley_subtle_wind(d=4.0, **_):
    t = tt(d)
    n = noise(d)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t)
    w = bp(n, 120, 600) * lfo
    e = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (d - t) / 0.5)
    return w * e * 0.6

def foley_sea_waves(d=5.0, **_):
    t = tt(d)
    n = noise(d)
    # Slow rolling Mediterranean harbor swells
    lfo = (np.sin(2 * np.pi * 0.3 * t) ** 2) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.12 * t))
    water = bp(n, 200, 1400) * lfo
    e = np.minimum(1.0, t / 0.5) * np.minimum(1.0, (d - t) / 0.5)
    return lp(water * e, 1800) * 0.75

def foley_wooden_creak(d=3.0, **_):
    t = tt(d)
    # Creaking wooden ship hull & dock timber
    f0 = 65.0 + 15.0 * np.sin(2 * np.pi * 1.5 * t)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    creak = np.sin(phase) * env(len(t), 0.05, 3.0)
    friction = bp(noise(d), 400, 1800) * (np.sin(2 * np.pi * 3.0 * t) ** 4) * 0.3
    e = np.minimum(1.0, t / 0.3) * np.minimum(1.0, (d - t) / 0.4)
    return lp((creak + friction) * e, 2200) * 0.7

def foley_fire_inferno(d=5.0, **_):
    t = tt(d)
    n = noise(d)
    roar = bp(n, 80, 500) * 0.65
    crackle = bp(n, 1200, 3800) * (rng.random(len(n)) < 0.004).astype(float) * 25.0
    total = roar + lp(crackle, 2500)
    e = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (d - t) / 0.4)
    return lp(total * e, 3200) * 0.85

def foley_dust_whisper(d=4.0, **_):
    t = tt(d)
    n = noise(d)
    subtle = bp(n, 600, 2200) * 0.25
    e = np.minimum(1.0, t / 0.5) * np.minimum(1.0, (d - t) / 0.5)
    return subtle * e * 0.5

def foley_quill_scratch(d=4.0, **_):
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
    e = np.minimum(1.0, t / 0.3) * np.minimum(1.0, (d - t) / 0.3)
    return lp(out * e, 4500) * 0.6

def foley_fire_crackle(d=4.5, **_):
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

def triumph_brass(d=4.0, **_):
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
    t = tt(d)
    partials = [(261.6, 1.0, 3.2), (523.25, 0.6, 4.0), (740.0, 0.4, 5.5), (1046.5, 0.25, 6.5)]
    bell = np.zeros(len(t))
    for f, amp, decay in partials:
        bell += np.sin(2 * np.pi * f * t) * amp * np.exp(-t * decay)
    return lp(bell, 3200) * 0.6

FX = dict(
    cinematic_impact=cinematic_impact,
    sub_drop=sub_drop,
    foley_subtle_wind=foley_subtle_wind,
    foley_sea_waves=foley_sea_waves,
    foley_wooden_creak=foley_wooden_creak,
    foley_fire_inferno=foley_fire_inferno,
    foley_dust_whisper=foley_dust_whisper,
    foley_quill_scratch=foley_quill_scratch,
    foley_fire_crackle=foley_fire_crackle,
    triumph_brass=triumph_brass,
    bell_toll=bell_toll,
)

LEVEL = dict(
    cinematic_impact=-9,
    sub_drop=-12,
    foley_subtle_wind=-22,
    foley_sea_waves=-18,
    foley_wooden_creak=-17,
    foley_fire_inferno=-14,
    foley_dust_whisper=-21,
    foley_quill_scratch=-18,
    foley_fire_crackle=-20,
    triumph_brass=-16,
    bell_toll=-18,
)


# ---------- Ancient Mediterranean Mystery Score ----------

def music_alexandria_mystery():
    t = np.arange(N) / SR
    x = np.zeros(N)
    bpm = 78.0
    beat = 60.0 / bpm
    bar = beat * 4.0

    # 1. Deep acoustic drone in A minor (A1 55 Hz + E2 82.4 Hz + A2 110 Hz)
    drone = (
        np.sin(2 * np.pi * 55.0 * t) * 0.45 +
        np.sin(2 * np.pi * 82.41 * t) * 0.35 +
        np.sin(2 * np.pi * 110.0 * t) * 0.25
    )
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.12 * t)
    x += drone * 0.35

    # 2. Ancient Dorian chord progression: Am -> Em -> F -> Dm
    chords = [
        [220.0, 261.63, 329.63], # Am
        [164.81, 246.94, 329.63], # Em
        [174.61, 220.0, 261.63], # F
        [146.83, 220.0, 293.66], # Dm
    ]
    n_bars = int(np.ceil(DUR / bar)) + 1
    for b in range(n_bars):
        st = int(b * bar * SR)
        if st >= N: break
        dur_b = min(bar, (N - st) / SR)
        pts = int(dur_b * SR)
        t_b = tt(dur_b)[:pts]
        ch = chords[b % len(chords)]
        e_bar = np.minimum(1.0, t_b / 0.6) * np.minimum(1.0, (dur_b - t_b) / 0.6)
        bar_snd = np.zeros(pts)
        for freq in ch:
            bar_snd += (
                np.sin(2 * np.pi * freq * t_b) +
                0.28 * np.sin(2 * np.pi * 2 * freq * t_b)
            ) * 0.15
        x[st:st + pts] += bar_snd * e_bar

    # 3. Ancient plucked lyre arpeggio
    for k in range(int(DUR / beat)):
        i = int(k * beat * SR)
        p_dur = 0.65
        pts = int(p_dur * SR)
        if i + pts < N:
            t_p = tt(p_dur)
            note_f = chords[(k // 4) % 4][k % 3] * 1.5
            pluck = (np.sin(2 * np.pi * note_f * t_p) + 0.4 * np.sin(4 * np.pi * note_f * t_p)) * env(pts, 0.003, 6.0) * 0.18
            x[i:i + pts] += pluck

    # 4. Outro swell (last 8 seconds)
    outro_start = max(0, int((DUR - 8.5) * SR))
    if outro_start < N:
        t_out = (np.arange(N - outro_start)) / SR
        harmonic = np.sin(2 * np.pi * 440.0 * t_out) * 0.15 * np.minimum(1.0, t_out / 2.5)
        x[outro_start:] += harmonic

    x = lp(x, 2800)
    fade = np.ones(N)
    fi = int(0.6 * SR)
    fade[:fi] *= np.linspace(0.3, 1.0, fi)
    fo = int(1.2 * SR)
    fade[-fo:] *= np.linspace(1.0, 0.0, fo)
    return x / (np.abs(x).max() + 1e-9) * fade

def load_audio(f):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).astype(np.float64)


# ---------- Mix Assembly ----------
mix = np.zeros((N, 2))

vf = P / 'data/narration.wav'
voice = None
if vf.exists():
    v = load_audio(vf)[:N]
    voice = np.zeros((N, 2))
    voice[:len(v)] = v
    rms = np.sqrt(np.mean(voice ** 2) + 1e-12)
    voice *= db(-19) / rms
    mix += voice

m = music_alexandria_mystery()
m = np.stack([m, m], 1) * db(-24 if voice is not None else -20)
if voice is not None:
    lev = np.abs(voice.mean(1))
    lev = signal.lfilter([1 - 0.9995], [1, -0.9995], lev)
    lev /= lev.max() + 1e-9
    m *= (1.0 - 0.50 * np.clip(lev * 2.8, 0, 1))[:, None]
mix += m

for c in cj.get('cues', []):
    fn = FX.get(c['type'])
    if not fn: continue
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

mix = np.tanh(mix * 1.15) / 1.15
mix *= db(-1) / (np.abs(mix).max() + 1e-9)
wavfile.write(P / 'data/mix.wav', SR, (mix * 32767).astype(np.int16))
print(f"data/mix.wav: {DUR:.2f} s · voice: {'yes' if voice is not None else 'NO'} · {len(cj.get('cues', []))} cues")
