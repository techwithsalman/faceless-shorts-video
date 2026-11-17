"""Prompt2Video AI — Master Orchestrator Engine
Your Prompt. Your Video. Powered by Local AI.
100% Free, Local, Offline ($0.00, No APIs, No Subscriptions).

Transforms any prompt into a complete broadcast-ready vertical or landscape MP4:
1. Script & Scene Planning (Local LLM / Semantic Architect)
2. Narration (Kokoro-82M ONNX)
3. Subtitle Alignment (Faster-Whisper)
4. Visual Generation (Stable Diffusion Turbo)
5. 2.5D Depth Parallax (Depth-Anything Small)
6. Procedural Foley Sound Design (Three-Layer Audio Mix)
7. Headless WebGL Capture & FFmpeg Compositing
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
STYLES_DIR = ROOT_DIR / "styles" / "beyond-history"
EXAMPLE_DIR = STYLES_DIR / "example"

# Cache Configuration
if os.environ.get("HF_HOME"):
    CACHE_DIR = Path(os.environ["HF_HOME"])
elif Path("D:/faceless-shorts-ai/cache").exists():
    CACHE_DIR = Path("D:/faceless-shorts-ai/cache")
elif Path("D:/").exists():
    CACHE_DIR = Path("D:/faceless-shorts-ai/cache")
else:
    CACHE_DIR = Path.home() / ".faceless-shorts" / "cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR)
os.environ["TORCH_HOME"] = str(CACHE_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)

# Locate Python venv
VENV_PYTHON = Path.home() / ".faceless-shorts" / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


def emit(ipc_mode, event_type, **kwargs):
    """Emits structured JSON event if IPC mode enabled, else prints formatted text."""
    payload = {"event": event_type, **kwargs}
    if ipc_mode:
        print(f"__P2V_EVENT__{json.dumps(payload)}", flush=True)
    else:
        msg = kwargs.get("message", "")
        pct = kwargs.get("percent", "")
        if pct != "":
            print(f"[{pct}%] {msg}", flush=True)
        elif msg:
            print(f">>> {msg}", flush=True)


def get_dimensions(aspect_ratio, resolution):
    """Calculates pixel width and height."""
    is_720 = "720" in str(resolution)
    if aspect_ratio == "16:9":
        return (1280, 720) if is_720 else (1920, 1080)
    elif aspect_ratio == "1:1":
        return (720, 720) if is_720 else (1080, 1080)
    else:  # 9:16 default
        return (720, 1280) if is_720 else (1080, 1920)


def sanitize_filename(name):
    """Sanitizes topic into a valid directory name."""
    s = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", s)[:40] or "prompt2video-short"


def setup_project_scaffold(project_dir, width, height):
    """Copies template files and configures canvas dimensions."""
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy essential directories
    for d in ["src", "tools", "fonts", "vendor"]:
        src_d = EXAMPLE_DIR / d
        dst_d = project_dir / d
        if src_d.exists() and not dst_d.exists():
            shutil.copytree(src_d, dst_d)

    # Copy index.html and update canvas dimensions
    index_src = EXAMPLE_DIR / "index.html"
    index_dst = project_dir / "index.html"
    if index_src.exists():
        content = index_src.read_text(encoding="utf-8")
        # Replace canvas width/height
        content = re.sub(r'<canvas id="cv" width="\d+" height="\d+"></canvas>',
                         f'<canvas id="cv" width="{width}" height="{height}"></canvas>',
                         content)
        index_dst.write_text(content, encoding="utf-8")

    # Update capture.mjs window size
    capture_dst = project_dir / "tools" / "capture.mjs"
    if capture_dst.exists():
        c_code = capture_dst.read_text(encoding="utf-8")
        c_code = re.sub(r"'--window-size=\d+,\d+'", f"'--window-size={width},{height}'", c_code)
        capture_dst.write_text(c_code, encoding="utf-8")

    # Create subdirectories
    (project_dir / "data").mkdir(exist_ok=True)
    (project_dir / "assets").mkdir(exist_ok=True)
    (project_dir / "renders").mkdir(exist_ok=True)
    (project_dir / "review").mkdir(exist_ok=True)


def build_shots_js(project_dir, script_data, width, height):
    """Generates custom shots.js tailored to script scenes and visual prompts."""
    scenes = script_data.get("scenes", [])
    shots_file = project_dir / "src" / "shots.js"
    
    # Camera movements rotation: slow zoom in, pan left, pan right, low tilt, pull back
    moves = [
        {"panX": 0.0, "panY": -0.04, "zoom": 1.12, "desc": "slow cinematic push-in"},
        {"panX": 0.05, "panY": 0.0, "zoom": 1.08, "desc": "gentle tracking right"},
        {"panX": -0.05, "panY": 0.0, "zoom": 1.10, "desc": "gentle tracking left"},
        {"panX": 0.0, "panY": 0.05, "zoom": 1.14, "desc": "slow upward tilt"},
        {"panX": 0.0, "panY": 0.0, "zoom": 1.06, "desc": "atmospheric hold"},
        {"panX": 0.0, "panY": -0.03, "zoom": 1.04, "desc": "slow pull-back finale"}
    ]

    shots_code = f"""// Auto-generated by Prompt2Video AI Engine
// Canvas: {width}x{height}
import {{ getAudioTime }} from './core/timing.js';
import {{ drawCaptions }} from './core/captions.js';
import {{ drawVignette, drawFilmGrain, clamp }} from './core/lib.js';

let scenes = [];
let cuts = [];
let loaded = false;

export async function preloadShots() {{
  if (loaded) return;
  const numScenes = {len(scenes)};
  for (let i = 1; i <= numScenes; i++) {{
    const numStr = String(i).padStart(2, '0');
    const img = new Image();
    const depth = new Image();
    img.src = `assets/scene_${{numStr}}.jpg`;
    depth.src = `assets/scene_${{numStr}}_depth.png`;
    await Promise.all([
      new Promise(r => {{ img.onload = r; img.onerror = r; }}),
      new Promise(r => {{ depth.onload = r; depth.onerror = r; }})
    ]);
    scenes.push({{ img, depth }});
  }}
  try {{
    const res = await fetch('data/lines.json');
    cuts = await res.json();
  }} catch (e) {{
    cuts = [];
  }}
  loaded = true;
}}

export function drawShot(ctx, W, H, t) {{
  if (!scenes.length) return;
  
  // Find current scene cut
  let idx = 0;
  if (cuts && cuts.length) {{
    for (let i = 0; i < cuts.length; i++) {{
      if (t >= cuts[i].start && t <= cuts[i].end) {{
        idx = i;
        break;
      }}
      if (t > cuts[i].end) idx = i;
    }}
  }}
  idx = Math.min(idx, scenes.length - 1);
  const cur = scenes[idx];
  const shotStart = cuts[idx] ? cuts[idx].start : 0;
  const shotEnd = cuts[idx] ? cuts[idx].end : (t + 5);
  const duration = Math.max(1, shotEnd - shotStart);
  const progress = clamp((t - shotStart) / duration, 0, 1);

  if (cur && cur.img && cur.img.complete && cur.img.naturalWidth > 0) {{
    const img = cur.img;
    const targetAspect = W / H;
    const imgAspect = img.width / img.height;
    let baseW, baseH;
    if (imgAspect > targetAspect) {{
      baseH = img.height;
      baseW = img.height * targetAspect;
    }} else {{
      baseW = img.width;
      baseH = img.width / targetAspect;
    }}
    
    // Smooth cinematic zoom and subtle pan
    const zoom = 1.0 + 0.08 * progress;
    const srcW = baseW / zoom;
    const srcH = baseH / zoom;
    const panOffset = (progress - 0.5) * 0.04 * img.width;
    const sx = clamp((img.width - srcW) * 0.5 + panOffset, 0, img.width - srcW);
    const sy = clamp((img.height - srcH) * 0.5, 0, img.height - srcH);

    ctx.drawImage(img, sx, sy, srcW, srcH, 0, 0, W, H);
  }} else {{
    ctx.fillStyle = '#0a0b0e';
    ctx.fillRect(0, 0, W, H);
  }}

  // Atmospheric film post-processing
  drawVignette(ctx, W, H, 0.45);
  drawFilmGrain(ctx, W, H, 0.04, t);

  // Lower-third synchronized subtitles
  drawCaptions(ctx, W, H, t);
}}
"""
    shots_file.write_text(shots_code, encoding="utf-8")


def run_pipeline(prompt, duration=45, aspect_ratio="9:16", resolution="1080p",
                 voice="bm_george", style="cinematic-documentary", output_dir=None,
                 ipc_mode=False):
    """Executes the full automated Prompt2Video generation pipeline."""
    t_start = time.time()
    
    # 1. Prepare Paths
    short_slug = sanitize_filename(prompt)
    if not output_dir:
        output_dir = ROOT_DIR / "renders" / short_slug
    else:
        output_dir = Path(output_dir)
    
    project_dir = ROOT_DIR / "workspace" / short_slug
    project_dir.mkdir(parents=True, exist_ok=True)
    
    width, height = get_dimensions(aspect_ratio, resolution)
    emit(ipc_mode, "init", percent=0, message=f"Initializing Prompt2Video AI ({width}x{height}, {voice})...",
         project=str(project_dir), output=str(output_dir))

    # 2. Stage: Script Generation
    emit(ipc_mode, "stage", stage="script", percent=5, message="Analyzing prompt and generating script...")
    script_file = project_dir / "script.json"
    
    # Import and run local_llm directly
    sys.path.insert(0, str(SCRIPTS_DIR))
    from local_llm import generate_structured_script
    script_data = generate_structured_script(
        prompt_text=prompt,
        duration=duration,
        style=style,
        voice=voice,
        aspect_ratio=aspect_ratio
    )
    
    # Adapt to root script.json format expected by voice.py
    root_script = {
        "title": script_data["title"],
        "voice": voice,
        "speed": script_data.get("speed", 1.16),
        "lead": 0.25,
        "outro": 0.35,
        "gap": 0.10,
        "lines": [
            {
                "text": sc["text"],
                "visual": sc["visual_prompt"]
            }
            for sc in script_data["scenes"]
        ]
    }
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "data").mkdir(parents=True, exist_ok=True)
    (project_dir / "renders").mkdir(parents=True, exist_ok=True)

    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(root_script, f, indent=2)

    with open(project_dir / "data" / "script.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2)

    emit(ipc_mode, "script_ready", percent=15, message=f"Script ready: {len(script_data['scenes'])} scenes planned.",
         title=script_data["title"], scenes=script_data["scenes"])

    # 3. Stage: Project Scaffolding
    setup_project_scaffold(project_dir, width, height)
    build_shots_js(project_dir, script_data, width, height)

    # 4. Stage: Voice Generation (Kokoro-82M ONNX)
    emit(ipc_mode, "stage", stage="voice", percent=20, message="Synthesizing Kokoro-82M documentary narration...")
    voice_py = SCRIPTS_DIR / "voice.py"
    cmd_voice = [str(VENV_PYTHON), str(voice_py), str(project_dir)]
    res_v = subprocess.run(cmd_voice, capture_output=True, text=True)
    if res_v.returncode != 0:
        emit(ipc_mode, "error", message=f"Voice synthesis error: {res_v.stderr}")
        return False
    emit(ipc_mode, "stage", stage="voice_done", percent=32, message="Narration synthesized successfully.")

    # 5. Stage: Subtitle Alignment (Faster-Whisper)
    emit(ipc_mode, "stage", stage="subtitles", percent=35, message="Aligning word-by-word subtitles with Faster-Whisper...")
    words_py = SCRIPTS_DIR / "words.py"
    cmd_words = [str(VENV_PYTHON), str(words_py), str(project_dir)]
    res_w = subprocess.run(cmd_words, capture_output=True, text=True)
    if res_w.returncode != 0:
        emit(ipc_mode, "error", message=f"Subtitle alignment error: {res_w.stderr}")
        return False
    emit(ipc_mode, "stage", stage="subtitles_done", percent=45, message="Word timestamps synchronized.")

    # 6. Stage: Visual Generation (SD-Turbo)
    emit(ipc_mode, "stage", stage="visuals", percent=50, message="Generating photorealistic 35mm scene images...")
    local_image_py = SCRIPTS_DIR / "local_image.py"
    cmd_img = [str(VENV_PYTHON), str(local_image_py), "--project", str(project_dir)]
    res_img = subprocess.run(cmd_img, capture_output=True, text=True)
    if res_img.returncode != 0:
        emit(ipc_mode, "error", message=f"Image generation error: {res_img.stderr}")
        return False
    emit(ipc_mode, "stage", stage="visuals_done", percent=70, message="All scene plates generated.")

    # 7. Stage: Depth Maps (Depth-Anything Small)
    emit(ipc_mode, "stage", stage="depth", percent=72, message="Computing depth maps for 2.5D parallax...")
    depth_py = SCRIPTS_DIR / "depth_estimator.py"
    cmd_depth = [str(VENV_PYTHON), str(depth_py), "--project", str(project_dir)]
    res_depth = subprocess.run(cmd_depth, capture_output=True, text=True)
    if res_depth.returncode != 0:
        emit(ipc_mode, "error", message=f"Depth estimation error: {res_depth.stderr}")
        return False
    emit(ipc_mode, "stage", stage="depth_done", percent=80, message="Depth parallax maps ready.")

    # 8. Stage: Audio Mix (Procedural Score + Foley Cues)
    emit(ipc_mode, "stage", stage="audio_mix", percent=82, message="Synthesizing score and Foley sound design...")
    # Generate sound cues
    subprocess.run(["node", "tools/capture.mjs", "cues"], cwd=str(project_dir), capture_output=True)
    # Run audio mix
    mix_py = project_dir / "tools" / "mix.py"
    cmd_mix = [str(VENV_PYTHON), str(mix_py), "."]
    res_mix = subprocess.run(cmd_mix, cwd=str(project_dir), capture_output=True, text=True)
    if res_mix.returncode != 0:
        emit(ipc_mode, "error", message=f"Audio mix error: {res_mix.stderr}")
        return False
    emit(ipc_mode, "stage", stage="audio_mix_done", percent=86, message="Audio score and Foley mixed.")

    # 9. Stage: Headless Chrome Render & FFmpeg Muxing
    out_mp4 = output_dir / f"{short_slug}.mp4"
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    emit(ipc_mode, "stage", stage="render", percent=88, message=f"Rendering {width}x{height} 30FPS MP4 video...")
    
    cmd_render = ["node", "tools/capture.mjs", "video", str(out_mp4)]
    res_render = subprocess.run(cmd_render, cwd=str(project_dir), capture_output=True, text=True)
    if res_render.returncode != 0 or not out_mp4.exists():
        emit(ipc_mode, "error", message=f"Rendering error: {res_render.stderr}")
        return False

    # 10. Contact Sheet Preview
    contact_sheet = output_dir / f"{short_slug}-contact.jpg"
    subprocess.run(["node", "tools/capture.mjs", "sheet", str(contact_sheet), "2.0", "6"],
                   cwd=str(project_dir), capture_output=True)

    # 11. Completion & Stats
    total_time = time.time() - t_start
    file_size_mb = round(out_mp4.stat().st_size / (1024 * 1024), 2)
    
    emit(ipc_mode, "done", percent=100,
         message=f"Video generated in {total_time:.1f}s ({file_size_mb} MB).",
         videoPath=str(out_mp4),
         contactSheet=str(contact_sheet) if contact_sheet.exists() else None,
         duration=duration,
         fileSizeMB=file_size_mb,
         title=script_data["title"])

    print(f"\n===========================================================", flush=True)
    print(f"  SUCCESS! Video ready: {out_mp4}", flush=True)
    print(f"  Duration: ~{duration}s | Resolution: {width}x{height} | Size: {file_size_mb} MB", flush=True)
    print(f"===========================================================\n", flush=True)
    return True


def main():
    parser = argparse.ArgumentParser(description="Prompt2Video AI — Master Orchestrator")
    parser.add_argument("--prompt", "-p", required=True, help="Video topic or prompt")
    parser.add_argument("--duration", "-d", type=int, default=45, help="Video duration in seconds")
    parser.add_argument("--aspect-ratio", "-a", default="9:16", choices=["9:16", "16:9", "1:1"])
    parser.add_argument("--resolution", "-r", default="1080p", choices=["720p", "1080p"])
    parser.add_argument("--voice", "-v", default="bm_george", help="Kokoro voice ID")
    parser.add_argument("--style", "-s", default="cinematic-documentary", help="Visual style")
    parser.add_argument("--output", "-o", default=None, help="Output directory or file path")
    parser.add_argument("--ipc-json", action="store_true", help="Emit single-line JSON events for Electron IPC")
    args = parser.parse_args()

    success = run_pipeline(
        prompt=args.prompt,
        duration=args.duration,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        voice=args.voice,
        style=args.style,
        output_dir=args.output,
        ipc_mode=args.ipc_json
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
