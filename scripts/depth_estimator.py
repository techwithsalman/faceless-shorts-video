"""Local Monocular Depth Estimator for 2.5D Parallax Historical Documentary Animation.
100% Free, Offline, Local ($0.00, No APIs, No Subscriptions).
Uses Depth-Anything Small (cached on D:\\faceless-shorts-ai\\cache) on CPU in ~8s per image.
"""
import argparse, os, sys, time
from pathlib import Path
from PIL import Image

# Ensure HF Cache points to D:\faceless-shorts-ai\cache to protect Drive C:
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

_DEPTH_PIPE = None


def get_depth_pipeline():
    global _DEPTH_PIPE
    if _DEPTH_PIPE is not None:
        return _DEPTH_PIPE

    import torch
    from transformers import pipeline
    device = 0 if torch.cuda.is_available() else -1
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"Loading Depth-Anything pipeline on {device_name} (cache: {CACHE_DIR})...", flush=True)
    t0 = time.time()
    pipe = pipeline(
        task="depth-estimation",
        model="LiheYoung/depth-anything-small-hf",
        device=device,
        model_kwargs={"cache_dir": str(CACHE_DIR)}
    )
    print(f"Depth pipeline ready in {time.time() - t0:.2f} s on {device_name}", flush=True)
    _DEPTH_PIPE = pipe
    return pipe


def estimate_depth(image_path, output_path=None):
    pipe = get_depth_pipeline()
    img_p = Path(image_path)
    if not img_p.exists():
        raise FileNotFoundError(f"Image not found: {img_p}")

    if output_path is None:
        output_path = img_p.parent / f"{img_p.stem}_depth.png"
    else:
        output_path = Path(output_path)

    t0 = time.time()
    img = Image.open(img_p).convert("RGB")
    depth = pipe(img)["depth"]
    # Ensure same resolution as source image
    depth = depth.resize(img.size, Image.Resampling.BILINEAR)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    depth.save(str(output_path))
    print(f"Depth map saved: {output_path} ({img.size[0]}x{img.size[1]}, {time.time() - t0:.2f} s)", flush=True)
    return str(output_path)


def estimate_project_depths(project_dir):
    p = Path(project_dir).resolve()
    assets_dir = p / "assets"
    if not assets_dir.exists():
        raise FileNotFoundError(f"No assets directory in {p}")

    import glob
    scene_images = sorted(glob.glob(str(assets_dir / "scene_*.jpg")))
    if not scene_images:
        # Fallback to any jpg
        scene_images = sorted([f for f in glob.glob(str(assets_dir / "*.jpg")) if not f.endswith("_depth.png")])

    print(f"Estimating depth maps for {len(scene_images)} scene assets in {assets_dir}...")
    outputs = []
    for img_path in scene_images:
        if "_depth" in img_path:
            continue
        stem = Path(img_path).stem
        out_depth = assets_dir / f"{stem}_depth.png"
        estimate_depth(img_path, out_depth)
        outputs.append(str(out_depth))

    print(f"All {len(outputs)} depth maps successfully generated in {assets_dir}")
    return outputs


def main():
    ap = argparse.ArgumentParser(description="Local Depth Estimator for 2.5D Parallax")
    ap.add_argument("--image", "-i", help="Single image file path")
    ap.add_argument("--output", "-o", help="Output depth map PNG path")
    ap.add_argument("--project", "-p", help="Project directory to process all assets/scene_*.jpg")
    args = ap.parse_args()

    if args.project:
        estimate_project_depths(args.project)
    elif args.image:
        estimate_depth(args.image, args.output)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
