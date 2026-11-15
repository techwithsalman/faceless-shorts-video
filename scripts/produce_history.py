"""End-to-End Automated Production Pipeline for Beyond History Historical Shorts.
100% Free, Local, Offline ($0, No Paid APIs, No Subscriptions).

Usage:
  # Generate a complete historical short from an existing project:
  py scripts/produce_history.py --project ~/faceless-shorts/marcus-aurelius

  # Generate a complete historical short from a topic name:
  py scripts/produce_history.py --name bank-dollar --topic "The Man Who Bought an Entire Bank for $1"

Options:
  --project, -p     Project directory path
  --name, -n        Short name (creates ~/faceless-shorts/<name> if --project not specified)
  --topic, -t       Historical topic title
  --character, -c   Base character prompt for consistency across all scenes
  --model, -m       Local image model: sd-turbo (default), lcm-dreamshaper, realistic-vision, sdxl-turbo
  --voice, -v       Kokoro voice identifier (default: bm_george - solemn British documentary voice)
  --speed           Voice speed multiplier (default: 1.02)
  --steps           Inference steps for image generation (default: 2 for sd-turbo)
  --skip-images     Skip local image generation if assets/ already has scene images
  --skip-audio      Skip voice & whisper generation if data/narration.wav exists
  --skip-render     Skip headless Chrome & FFmpeg rendering
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
STYLES_DIR = ROOT_DIR / "styles" / "beyond-history"
EXAMPLE_DIR = STYLES_DIR / "example"

# Ensure FFmpeg and Python venv are discoverable in PATH
for candidate in [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-essentials_build" / "bin",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-full_build" / "bin",
]:
    if candidate.exists() and str(candidate) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")

VENV_PYTHON = Path(os.environ.get("USERPROFILE", "")) / ".faceless-shorts" / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path.home() / ".faceless-shorts" / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


def log(msg, step=None):
    prefix = f"[STEP {step}] " if step else ">>> "
    print(f"\n{prefix}{msg}", flush=True)


def run_cmd(cmd, cwd=None, desc=""):
    if desc:
        print(f"--- Running: {desc} ---", flush=True)
    res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=os.environ, shell=isinstance(cmd, str))
    if res.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {res.returncode}: {cmd}")
    return res


def ensure_project(project_dir, name="historical-short", topic=""):
    p = Path(project_dir).resolve()
    if not p.exists():
        log(f"Creating project directory: {p}", step=1)
        p.mkdir(parents=True, exist_ok=True)
        # Copy template files from beyond-history example
        for item in ["index.html", "src", "fonts", "tools"]:
            src_item = EXAMPLE_DIR / item
            dst_item = p / item
            if src_item.is_dir():
                shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            elif src_item.is_file():
                shutil.copy2(src_item, dst_item)

        (p / "assets").mkdir(exist_ok=True)
        (p / "data").mkdir(exist_ok=True)
        (p / "renders").mkdir(exist_ok=True)
        (p / "review").mkdir(exist_ok=True)

        # Copy fallback master asset if available
        fb_src = EXAMPLE_DIR / "assets" / "marcus_aurelius.jpg"
        if fb_src.exists():
            shutil.copy2(fb_src, p / "assets" / "marcus_aurelius.jpg")

    script_path = p / "script.json"
    if not script_path.exists():
        log(f"Initializing script.json for topic: {topic or name}", step=1)
        initial_script = {
            "title": topic or name.replace("-", " ").title(),
            "voice": "bm_george",
            "speed": 1.02,
            "lead": 0.3,
            "outro": 0.8,
            "gap": 0.2,
            "music": "tension",
            "character": "weathered 50-year-old Mediterranean man with beard and brown eyes, living human actor, authentic period armor",
            "lines": [
                {
                    "text": f"In the forgotten archives of history, one story defies belief.",
                    "visual": "close-up of an ancient illuminated manuscript under flickering candlelight, 35mm film photograph"
                },
                {
                    "text": "A ruler faced impossible odds and risked an entire empire.",
                    "visual": "weathered stoic commander standing on a misty ancient battlefield at dusk, campfires burning"
                },
                {
                    "text": "Yet his greatest victory was not fought with swords,",
                    "visual": "ancient royal council chamber, heavy bronze armor, stone pillars, shadow and torchlight"
                },
                {
                    "text": "but decided in the quiet discipline of the mind.",
                    "visual": "dramatic close-up of stoic commander eyes, firelight reflection, shallow depth of field",
                    "gap": 0.3
                }
            ]
        }
        script_path.write_text(json.dumps(initial_script, indent=2), encoding="utf-8")

    return p


def produce(project_dir, topic="", character="", model="sd-turbo", voice="bm_george", speed=1.02,
            skip_images=False, skip_audio=False, skip_render=False, steps=2):
    t_start = time.time()
    p = Path(project_dir).resolve()
    log(f"Producing Beyond History Short in: {p}")

    script_file = p / "script.json"
    if not script_file.exists():
        raise FileNotFoundError(f"Missing script.json in {p}")

    script = json.loads(script_file.read_text(encoding="utf-8"))
    if voice:
        script["voice"] = voice
    if speed:
        script["speed"] = speed
    if character:
        script["character"] = character
    script_file.write_text(json.dumps(script, indent=2), encoding="utf-8")

    # 1. Kokoro Voice Generation
    narration_wav = p / "data" / "narration.wav"
    if not skip_audio or not narration_wav.exists():
        log("Generating voiceover with local Kokoro-82M ONNX...", step=2)
        voice_script = SCRIPTS_DIR / "voice.py"
        run_cmd([str(VENV_PYTHON), str(voice_script), str(p)], desc="Kokoro TTS")
    else:
        log("Skipping voice generation (narration.wav exists)", step=2)

    # 2. Faster-Whisper Subtitle Alignment
    words_json = p / "data" / "words.json"
    if not skip_audio or not words_json.exists():
        log("Extracting word timestamps with local Faster-Whisper...", step=3)
        words_script = SCRIPTS_DIR / "words.py"
        run_cmd([str(VENV_PYTHON), str(words_script), str(p)], desc="Faster-Whisper Subtitle Sync")
    else:
        log("Skipping Whisper alignment (words.json exists)", step=3)

    # 3. Local Open-Weight Visual Generation
    if not skip_images:
        log(f"Generating photorealistic scene assets locally using '{model}'...", step=4)
        local_image_script = SCRIPTS_DIR / "local_image.py"
        img_cmd = [
            str(VENV_PYTHON), str(local_image_script),
            "--project", str(p),
            "--model", model,
            "--steps", str(steps)
        ]
        if character or script.get("character"):
            img_cmd.extend(["--character", character or script.get("character")])
        run_cmd(img_cmd, desc=f"Local AI Image Generation ({model})")

        # 3b. Monocular Depth Estimation for 2.5D Parallax
        log("Estimating monocular depth maps for 2.5D parallax motion...", step="4b")
        depth_script = SCRIPTS_DIR / "depth_estimator.py"
        run_cmd([str(VENV_PYTHON), str(depth_script), "--project", str(p)], desc="Monocular Depth Estimation")
    else:
        log("Skipping image generation (--skip-images specified)", step=4)

    # 4. Cues and Audio Mixing
    log("Computing transition cues and mixing procedural documentary soundtrack...", step=5)
    capture_mjs = p / "tools" / "capture.mjs"
    mix_py = p / "tools" / "mix.py"

    run_cmd(["node", str(capture_mjs), "check"], cwd=p, desc="Scene Check")
    run_cmd(["node", str(capture_mjs), "cues"], cwd=p, desc="Generate Cues")
    run_cmd([str(VENV_PYTHON), str(mix_py), "."], cwd=p, desc="Atmospheric Soundtrack Mixing")

    # 5. FFmpeg Headless Chrome Render
    if not skip_render:
        short_name = p.name
        out_mp4 = p / "renders" / f"{short_name}.mp4"
        log(f"Rendering final 1080x1920 30 FPS MP4 to: {out_mp4}...", step=6)
        run_cmd(["node", str(capture_mjs), "video", f"renders/{short_name}.mp4"], cwd=p, desc="FFmpeg MP4 Capture")

        # QA Sheet
        sheet_jpg = p / "review" / "all.jpg"
        log(f"Generating timestamped QA contact sheet: {sheet_jpg}...", step=7)
        run_cmd(["node", str(capture_mjs), "sheet", "review/all.jpg", "0.5", "10"], cwd=p, desc="QA Contact Sheet")

        elapsed = time.time() - t_start
        log(f"SUCCESS: Beyond History Short rendered in {elapsed:.1f} s!\nOutput: {out_mp4}\nContact Sheet: {sheet_jpg}")
        return str(out_mp4)
    else:
        log("Skipping render (--skip-render specified)", step=6)
        return str(p)


def main():
    ap = argparse.ArgumentParser(description="Produce Beyond History YouTube Shorts using 100% Free Local AI")
    ap.add_argument("--project", "-p", help="Path to project directory")
    ap.add_argument("--name", "-n", help="Short name (created under ~/faceless-shorts/ if --project omitted)")
    ap.add_argument("--topic", "-t", default="", help="Historical documentary topic title")
    ap.add_argument("--character", "-c", default="", help="Base character prompt for consistency")
    ap.add_argument("--model", "-m", default="sd-turbo", choices=["sd-turbo", "lcm-dreamshaper", "realistic-vision", "sdxl-turbo"], help="Local image model")
    ap.add_argument("--voice", "-v", default="bm_george", help="Kokoro voice (default: bm_george)")
    ap.add_argument("--speed", type=float, default=1.02, help="Voice speed (default: 1.02)")
    ap.add_argument("--steps", type=int, default=2, help="Inference steps for image generation (default: 2)")
    ap.add_argument("--skip-images", action="store_true", help="Skip image generation")
    ap.add_argument("--skip-audio", action="store_true", help="Skip voice and whisper sync")
    ap.add_argument("--skip-render", action="store_true", help="Skip FFmpeg MP4 export")

    args = ap.parse_args()

    if not args.project:
        if not args.name:
            if args.topic:
                args.name = "".join(c if c.isalnum() else "-" for c in args.topic.lower()).strip("-")
            else:
                args.name = "beyond-history-short"
        proj_dir = Path.home() / "faceless-shorts" / args.name
    else:
        proj_dir = Path(args.project)

    proj_dir = ensure_project(proj_dir, name=args.name or proj_dir.name, topic=args.topic)
    produce(
        project_dir=proj_dir,
        topic=args.topic,
        character=args.character,
        model=args.model,
        voice=args.voice,
        speed=args.speed,
        skip_images=args.skip_images,
        skip_audio=args.skip_audio,
        skip_render=args.skip_render,
        steps=args.steps,
    )


if __name__ == "__main__":
    main()
