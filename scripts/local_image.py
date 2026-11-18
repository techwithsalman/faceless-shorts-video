"""Local open-weight AI image generator for historical documentaries ($0, completely offline).

Usage:
  # Generate a single scene image:
  python scripts/local_image.py --prompt "Roman Emperor Marcus Aurelius in armor" --output scene1.jpg

  # Generate 9:16 vertical images:
  python scripts/local_image.py --prompt "..." --output scene.jpg --width 512 --height 768

  # Generate multiple scenes from a project script.json:
  python scripts/local_image.py --project ~/faceless-shorts/my-short

Models supported (all 100% free and open-weight):
  --model sd-turbo          (default, ultra-fast 1-2 step CPU inference in 4-8 s)
  --model lcm-dreamshaper   (4-step high-quality cinematic portraits)
  --model realistic-vision  (SD 1.5 photorealistic historical model)
  --model sdxl-turbo        (SDXL high resolution 1-step)
"""
import argparse, json, os, sys, time
from pathlib import Path

# Cache directory configuration: respects HF_HOME, then D:\faceless-shorts-ai\cache, then ~/.faceless-shorts/cache
if os.environ.get("HF_HOME"):
    CACHE_DIR = Path(os.environ["HF_HOME"])
elif Path("D:/").exists():
    CACHE_DIR = Path("D:/faceless-shorts-ai/cache")
else:
    CACHE_DIR = Path.home() / ".faceless-shorts" / "cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR)
os.environ["TORCH_HOME"] = str(CACHE_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)

import torch
from diffusers import AutoPipelineForText2Image, DPMSolverMultistepScheduler

MODELS = {
    "sd-turbo": "stabilityai/sd-turbo",
    "lcm-dreamshaper": "SimianLuo/LCM_Dreamshaper_v7",
    "realistic-vision": "SG161222/Realistic_Vision_V6.0_B1_noVAE",
    "sdxl-turbo": "stabilityai/sdxl-turbo",
}

_PIPE = None
_CURRENT_MODEL = None


def get_pipeline(model_key="sd-turbo"):
    global _PIPE, _CURRENT_MODEL
    if _PIPE is not None and _CURRENT_MODEL == model_key:
        return _PIPE

    model_id = MODELS.get(model_key, model_key)
    has_cuda = torch.cuda.is_available()
    device = "cuda" if has_cuda else "cpu"
    dtype = torch.float16 if has_cuda else torch.float32

    print(f"Loading local model '{model_id}' on {device.upper()} (cache: {CACHE_DIR})...", flush=True)
    t0 = time.time()

    load_kwargs = {
        "cache_dir": str(CACHE_DIR),
        "torch_dtype": dtype,
    }
    if has_cuda:
        load_kwargs["variant"] = "fp16"

    pipe = AutoPipelineForText2Image.from_pretrained(model_id, **load_kwargs)
    pipe.to(device)

    # Memory optimizations for lower-end hardware
    if not has_cuda:
        pipe.enable_attention_slicing()

    print(f"Model ready in {time.time() - t0:.2f} s", flush=True)
    _PIPE = pipe
    _CURRENT_MODEL = model_key
    return pipe


def generate_image(prompt, output_path, model="sd-turbo", width=512, height=768, steps=None, guidance=None, seed=None, negative=""):
    pipe = get_pipeline(model)
    has_cuda = torch.cuda.is_available()

    # Model-specific defaults
    if steps is None:
        if model in ("sd-turbo", "sdxl-turbo"):
            steps = 2
        elif model == "lcm-dreamshaper":
            steps = 4
        else:
            steps = 20 if has_cuda else 12

    if guidance is None:
        if model in ("sd-turbo", "sdxl-turbo"):
            guidance = 0.0
        elif model == "lcm-dreamshaper":
            guidance = 1.5
        else:
            guidance = 7.0

    gen = None
    if seed is not None:
        gen = torch.Generator(device=pipe.device).manual_seed(seed)

    print(f"Generating image: '{prompt[:55]}...' ({width}x{height}, steps={steps}, guidance={guidance})", flush=True)
    t0 = time.time()

    call_kwargs = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": steps,
        "guidance_scale": guidance,
        "generator": gen,
    }
    if negative and model not in ("sd-turbo", "sdxl-turbo"):
        call_kwargs["negative_prompt"] = negative

    out = pipe(**call_kwargs).images[0]
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(out_p))
    print(f"Saved: {out_p} ({time.time() - t0:.2f} s)", flush=True)
    return str(out_p)


def generate_project_scenes(project_dir, model="sd-turbo", char_prompt="", width=512, height=512):
    p = Path(project_dir)
    script_file = p / "script.json"
    if not script_file.exists():
        raise SystemExit(f"No script.json found in {p}")

    S = json.loads(script_file.read_text())
    lines = S.get("lines", [])
    assets_dir = p / "assets"
    assets_dir.mkdir(exist_ok=True)

    print(f"Generating scenes for '{S.get('title', p.name)}' ({len(lines)} cuts)...")
    base_character = char_prompt or S.get("character", "weathered 50-year-old Mediterranean man with beard and brown eyes, living human actor, authentic bronze Roman armor")

    outputs = []
    for i, ln in enumerate(lines):
        txt = ln.get("text", "")
        visual = ln.get("visual", "")
        # Build cinematic documentary prompt combining consistent character + scene action
        if any(w in (visual or txt).lower() for w in ("portrait", "face", "man", "emperor", "he", "stare", "close-up", "eyes")):
            full_prompt = f"Cinematic historical documentary still, close-up photograph of {base_character}, {visual or txt}, realistic skin pores, living human, dramatic chiaroscuro candlelight, 35mm film photograph, historical drama, masterpiece"
        else:
            full_prompt = f"Cinematic historical documentary wide shot, {visual or txt}, authentic historical setting, natural lighting, atmospheric fog and smoke, 35mm film photograph, masterpiece"

        out_file = assets_dir / f"scene_{i+1:02d}.jpg"
        generate_image(
            prompt=full_prompt,
            output_path=str(out_file),
            model=model,
            width=width,
            height=height,
            seed=42 + i, # Fixed seed sequence for character consistency
        )
        outputs.append(str(out_file))

    print(f"All {len(outputs)} scene images generated in {assets_dir}")
    return outputs


def main():
    ap = argparse.ArgumentParser(description="Local Free AI Image Generator for Historical Shorts")
    ap.add_argument("--prompt", help="Text prompt describing the historical scene")
    ap.add_argument("--output", "-o", default="D:/faceless-shorts-ai/output.jpg", help="Output image file path")
    ap.add_argument("--project", help="Project directory to generate scenes for from script.json")
    ap.add_argument("--model", default="sd-turbo", choices=list(MODELS.keys()), help="Model to use")
    ap.add_argument("--width", type=int, default=512, help="Width in pixels (default: 512)")
    ap.add_argument("--height", type=int, default=512, help="Height in pixels (default: 512)")
    ap.add_argument("--steps", type=int, help="Inference steps")
    ap.add_argument("--guidance", type=float, help="CFG guidance scale")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for consistency")
    ap.add_argument("--negative", default="cartoon, 3d render, anime, deformed, bad anatomy, low quality", help="Negative prompt")
    ap.add_argument("--character", default="", help="Base character prompt to preserve consistency")

    args = ap.parse_args()

    if args.project:
        generate_project_scenes(
            args.project,
            model=args.model,
            char_prompt=args.character,
            width=args.width,
            height=args.height,
        )
    elif args.prompt:
        generate_image(
            prompt=args.prompt,
            output_path=args.output,
            model=args.model,
            width=args.width,
            height=args.height,
            steps=args.steps,
            guidance=args.guidance,
            seed=args.seed,
            negative=args.negative,
        )
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
