"""Beyond History: The Terracotta Army Documentary Soundtrack Engine
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
rng = np.random.default_rng(210)
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


# ---------- Foley Effects Tailored for Terracotta Army ----------

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

def foley_shovel_strike(d=2.0, **_):
    t = tt(d)
    # Shovel metal blade striking hard clay + dirt crunch
    clink = np.sin(2 * np.pi * 1450.0 * t) * env(len(t), 0.002, 14.0) * 0.65
    scrape = bp(noise(d), 800, 3200) * env(len(t), 0.005, 8.0) * 0.8
    thud = lp(noise(d), 180) * env(len(t), 0.002, 10.0) * 0.9
    return np.tanh(1.5 * (clink + scrape + thud)) * 0.9

def foley_ancient_halls(d=5.0, **_):
    t = tt(d)
    n = noise(d)
    subtle_air = bp(n, 90, 420) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.18 * t))
    e = np.minimum(1.0, t / 0.5) * np.minimum(1.0, (d - t) / 0.5)
    return subtle_air * e * 0.65

def foley_clay_clink(d=3.0, **_):
    t = tt(d)
    out = np.zeros(len(t))
    for k in range(3):
        st = int((0.15 + k * 0.6) * SR)
        dur_c = 0.25
        n_pts = int(dur_c * SR)
        if st + n_pts < len(out):
            t_c = np.arange(n_pts) / SR
            f_c = 920.0 + k * 180.0
            clink = (np.sin(2 * np.pi * f_c * t_c) + 0.3 * np.sin(4 * np.pi * f_c * t_c)) * env(n_pts, 0.002, 18.0) * 0.35
            out[st:st + n_pts] += clink
    return out * 0.75

def guzheng_pluck(d=4.0, **_):
    t = tt(d)
    # Ancient Chinese pentatonic plucked string (Guzheng)
    notes = [196.0, 220.0, 261.63, 293.66, 329.63]
    out = np.zeros(len(t))
    for k, freq in enumerate(notes[:3]):
        st = int(k * 0.45 * SR)
        dur_p = 1.2
        n_pts = int(dur_p * SR)
        if st + n_pts < len(out):
            t_p = np.arange(n_pts) / SR
            p = (np.sin(2 * np.pi * freq * t_p) + 0.35 * np.sin(4 * np.pi * freq * t_p)) * env(n_pts, 0.003, 6.0) * 0.25
            out[st:st + n_pts] += p
    return lp(out, 3200) * 0.8

def foley_mercury_drip(d=4.5, **_):
    t = tt(d)
    out = np.zeros(len(t))
    n_drips = int(d * 4)
    locs = rng.integers(0, max(1, len(t) - int(0.1 * SR)), size=n_drips)
    for loc in locs:
        dur_d = 0.08
        pts = int(dur_d * SR)
        t_d = np.arange(pts) / SR
        f_d = rng.uniform(450, 850)
        plop = np.sin(2 * np.pi * (f_d + 300.0 * np.exp(-t_d * 25.0)) * t_d) * env(pts, 0.002, 14.0) * 0.35
        out[loc:loc + pts] += plop
    e = np.minimum(1.0, t / 0.4) * np.minimum(1.0, (d - t) / 0.4)
    return out * e * 0.75

def chinese_bell(d=5.0, **_):
    t = tt(d)
    # Ancient Chinese bronze bianzhong bell chime
    partials = [(220.0, 1.0, 2.8), (440.0, 0.55, 3.5), (660.0, 0.35, 4.2), (880.0, 0.20, 5.0)]
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

def foley_dust_whisper(d=4.0, **_):
    t = tt(d)
    n = noise(d)
    subtle = bp(n, 600, 2200) * 0.25
    e = np.minimum(1.0, t / 0.5) * np.minimum(1.0, (d - t) / 0.5)
    return subtle * e * 0.5

def foley_palace_fire(d=4.5, **_):
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

FX = dict(
    cinematic_impact=cinematic_impact,
    sub_drop=sub_drop,
    foley_shovel_strike=foley_shovel_strike,
    foley_ancient_halls=foley_ancient_halls,
    foley_clay_clink=foley_clay_clink,
    guzheng_pluck=guzheng_pluck,
    foley_mercury_drip=foley_mercury_drip,
    chinese_bell=chinese_bell,
    triumph_brass=triumph_brass,
    foley_dust_whisper=foley_dust_whisper,
    foley_palace_fire=foley_palace_fire,
)

LEVEL = dict(
    cinematic_impact=-9,
    sub_drop=-12,
    foley_shovel_strike=-8,
    foley_ancient_halls=-20,
    foley_clay_clink=-16,
    guzheng_pluck=-15,
    foley_mercury_drip=-17,
    chinese_bell=-16,
    triumph_brass=-16,
    foley_dust_whisper=-21,
    foley_palace_fire=-20,
)


# ---------- Terracotta Mystery Score ----------

def music_terracotta_mystery():
    t = np.arange(N) / SR
    x = np.zeros(N)
    bpm = 76.0
    beat = 60.0 / bpm
    bar = beat * 4.0

    # 1. Subterranean drone in D (D1 36.7 Hz + A1 55.0 Hz + D2 73.4 Hz)
    drone = (
        np.sin(2 * np.pi * 36.71 * t) * 0.45 +
        np.sin(2 * np.pi * 55.0 * t) * 0.35 +
        np.sin(2 * np.pi * 73.42 * t) * 0.25
    )
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.12 * t)
    x += drone * 0.35

    # 2. Ancient pentatonic progression: D -> F -> G -> A
    pentatonic = [146.83, 174.61, 196.0, 220.0]
    n_bars = int(np.ceil(DUR / bar)) + 1
    for b in range(n_bars):
        st = int(b * bar * SR)
        if st >= N: break
        dur_b = min(bar, (N - st) / SR)
        pts = int(dur_b * SR)
        t_b = tt(dur_b)[:pts]
        f_b = pentatonic[b % len(pentatonic)]
        e_bar = np.minimum(1.0, t_b / 0.6) * np.minimum(1.0, (dur_b - t_b) / 0.6)
        bar_snd = (np.sin(2 * np.pi * f_b * t_b) + 0.3 * np.sin(4 * np.pi * f_b * t_b)) * 0.18
        x[st:st + pts] += bar_snd * e_bar

    # 3. Soft wooden pulse
    for k in range(int(DUR / beat)):
        if k % 2 == 0:
            i = int(k * beat * SR)
            p_dur = 0.4
            pts = int(p_dur * SR)
            if i + pts < N:
                t_p = tt(p_dur)
                pulse = np.sin(2 * np.pi * 65.0 * t_p) * env(pts, 0.005, 7.0) * 0.25
                x[i:i + pts] += pulse

    # 4. Outro swell
    outro_start = max(0, int((DUR - 8.5) * SR))
    if outro_start < N:
        t_out = (np.arange(N - outro_start)) / SR
        swell = np.sin(2 * np.pi * 293.66 * t_out) * 0.16 * np.minimum(1.0, t_out / 2.5)
        x[outro_start:] += swell

    x = lp(x, 2800)
    fade = np.ones(N)
    fi = int(0.6 * SR)
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

m = music_terracotta_mystery()
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
