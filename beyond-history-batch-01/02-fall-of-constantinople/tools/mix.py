"""Beyond History: The Fall of Constantinople (1453) Documentary Soundtrack Engine
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
rng = np.random.default_rng(1453)
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


# ---------- Foley Effects Tailored for Constantinople ----------

def cinematic_impact(d=2.2, **_):
    t = tt(d)
    f = 85.0 * np.exp(-t * 2.8) + 32.0
    phase = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(phase) * env(len(t), 0.004, 3.5)
    blast = lp(noise(d), 140) * env(len(t), 0.002, 6.0) * 0.75
    raw = sub * 0.8 + blast
    return np.tanh(1.8 * raw) * 0.95

def foley_cannon_blast(d=3.5, **_):
    t = tt(d)
    # Massive gunpowder explosion + sub boom
    f_sub = 95.0 * np.exp(-t * 5.0) + 28.0
    sub = np.sin(2 * np.pi * np.cumsum(f_sub) / SR) * env(len(t), 0.002, 3.5)
    blast = lp(noise(d), 450) * env(len(t), 0.001, 8.0) * 1.5
    crackle = bp(noise(d), 800, 3000) * env(len(t), 0.01, 14.0) * 0.6
    total = np.tanh(1.8 * (sub * 0.85 + blast + crackle))
    e = np.minimum(1.0, (d - t) / 0.5)
    return total * e * 0.95

def foley_stone_collapse(d=4.0, **_):
    t = tt(d)
    n = noise(d)
    # Heavy stone masonry tumbling & crashing
    rumble = lp(n, 180) * env(len(t), 0.1, 2.5) * 0.8
    shatter = bp(n, 600, 2400) * env(len(t), 0.05, 5.0) * 0.4
    e = np.minimum(1.0, t / 0.2) * np.minimum(1.0, (d - t) / 0.5)
    return (rumble + shatter) * e * 0.75

def foley_galley_rollers(d=5.0, **_):
    t = tt(d)
    # Greased timber groaning + rhythmic heave cadence
    f0 = 55.0 + 12.0 * np.sin(2 * np.pi * 1.2 * t)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    groan = np.sin(phase) * 0.4
    friction = bp(noise(d), 300, 1600) * (np.sin(2 * np.pi * 1.2 * t) ** 2) * 0.35
    e = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (d - t) / 0.4)
    return (groan + friction) * e * 0.7

def war_drum(d=1.5, **_):
    t = tt(d)
    f = 65.0 * np.exp(-t * 7.0) + 45.0
    membrane = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.003, 4.5)
    slap = lp(noise(d), 280) * env(len(t), 0.002, 12.0) * 0.75
    return np.tanh(1.5 * (membrane + slap)) * 0.85

def foley_greek_fire(d=4.5, **_):
    t = tt(d)
    n = noise(d)
    roar = bp(n, 140, 700) * 0.6
    sputter = bp(n, 1200, 3600) * (rng.random(len(n)) < 0.005).astype(float) * 20.0
    e = np.minimum(1.0, t / 0.3) * np.minimum(1.0, (d - t) / 0.4)
    return lp((roar + lp(sputter, 2200)) * e, 2800) * 0.75

def foley_sword_draw(d=2.0, **_):
    t = tt(d)
    # Metallic steel blade friction shing
    f = 1800.0 * np.exp(-t * 2.0) + 900.0
    blade = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.005, 7.0) * 0.35
    friction = bp(noise(d), 1200, 4200) * env(len(t), 0.01, 8.0) * 0.5
    return lp(blade + friction, 4200) * 0.75

def byzantine_bell(d=5.0, **_):
    t = tt(d)
    # Resonant church bell chime (Hagia Sophia)
    partials = [(174.6, 1.0, 2.5), (349.2, 0.6, 3.2), (523.2, 0.45, 4.0), (698.4, 0.25, 5.0)]
    bell = np.zeros(len(t))
    for f, amp, decay in partials:
        bell += np.sin(2 * np.pi * f * t) * amp * np.exp(-t * decay)
    return lp(bell, 2800) * 0.75

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

def foley_siege_wind(d=4.5, **_):
    t = tt(d)
    n = noise(d)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.28 * t)
    w = bp(n, 140, 650) * lfo
    e = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (d - t) / 0.5)
    return w * e * 0.55

FX = dict(
    cinematic_impact=cinematic_impact,
    foley_cannon_blast=foley_cannon_blast,
    foley_stone_collapse=foley_stone_collapse,
    foley_galley_rollers=foley_galley_rollers,
    war_drum=war_drum,
    foley_greek_fire=foley_greek_fire,
    foley_sword_draw=foley_sword_draw,
    byzantine_bell=byzantine_bell,
    triumph_brass=triumph_brass,
    foley_siege_wind=foley_siege_wind,
)

LEVEL = dict(
    cinematic_impact=-9,
    foley_cannon_blast=-7,
    foley_stone_collapse=-14,
    foley_galley_rollers=-16,
    war_drum=-10,
    foley_greek_fire=-15,
    foley_sword_draw=-15,
    byzantine_bell=-17,
    triumph_brass=-16,
    foley_siege_wind=-22,
)


# ---------- Constantinople Epic Score ----------

def music_constantinople_epic():
    t = np.arange(N) / SR
    x = np.zeros(N)
    bpm = 80.0
    beat = 60.0 / bpm
    bar = beat * 4.0

    # 1. Low war drone in D minor (D1 36.7 Hz + D2 73.4 Hz + A2 110 Hz)
    drone = (
        np.sin(2 * np.pi * 36.71 * t) * 0.45 +
        np.sin(2 * np.pi * 73.42 * t) * 0.40 +
        np.sin(2 * np.pi * 110.0 * t) * 0.25
    )
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.15 * t)
    x += drone * 0.35

    # 2. Epic war chord progression: Dm -> Bb -> Gm -> A
    chords = [
        [146.83, 174.61, 220.0],
        [116.54, 174.61, 233.08],
        [98.0, 146.83, 196.0],
        [110.0, 164.81, 220.0],
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
                0.35 * np.sin(2 * np.pi * 2 * freq * t_b)
            ) * 0.18
        x[st:st + pts] += bar_snd * e_bar

    # 3. Heavy military timpani/davul pulse on beats 1 and 3
    for k in range(int(DUR / beat)):
        if k % 2 == 0:
            i = int(k * beat * SR)
            p_dur = 0.55
            pts = int(p_dur * SR)
            if i + pts < N:
                t_p = tt(p_dur)
                pulse_f = 65.0 * np.exp(-t_p * 6.0) + 48.0
                pulse = np.sin(2 * np.pi * np.cumsum(pulse_f) / SR) * env(pts, 0.005, 5.0) * 0.30
                x[i:i + pts] += pulse

    # 4. Outro brass swell
    outro_start = max(0, int((DUR - 9.0) * SR))
    if outro_start < N:
        t_out = (np.arange(N - outro_start)) / SR
        brass = (np.sin(2 * np.pi * 293.66 * t_out) * 0.18 + np.sin(2 * np.pi * 440.0 * t_out) * 0.12) * np.minimum(1.0, t_out / 2.5)
        x[outro_start:] += brass

    x = lp(x, 2800)
    fade = np.ones(N)
    fi = int(0.5 * SR)
    fade[:fi] *= np.linspace(0.4, 1.0, fi)
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

m = music_constantinople_epic()
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
