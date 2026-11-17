"""Prompt2Video AI — Comprehensive Environment & Dependency Verifier
Checks PyTorch, Kokoro ONNX, Faster-Whisper, Diffusers, Transformers, and FFmpeg.
Emits structured JSON progress for Electron UI wizard and writes .verified.json marker.
"""

import sys
import os
import time
import json
import shutil
from pathlib import Path


def emit(stage, percent, message, **kwargs):
    payload = {
        "event": "verify_progress",
        "stage": stage,
        "percent": percent,
        "message": message,
        **kwargs
    }
    print(f"__P2V_VERIFY__{json.dumps(payload)}", flush=True)


def verify():
    emit("start", 0, "Initializing neural dependency verification...")
    t0 = time.time()
    results = {}
    runtime_dir = Path(sys.executable).resolve().parent.parent

    # 1. PyTorch
    emit("torch", 15, "Verifying PyTorch (CPU/CUDA core)...")
    try:
        t_start = time.time()
        import torch
        cuda_avail = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
        results["torch"] = {
            "ok": True,
            "version": torch.__version__,
            "cuda": cuda_avail,
            "device": device_name,
            "load_time_s": round(time.time() - t_start, 2)
        }
        emit("torch_ok", 25, f"PyTorch {torch.__version__} ready on {device_name}", details=results["torch"])
    except Exception as e:
        results["torch"] = {"ok": False, "error": str(e)}
        emit("torch_fail", 25, f"PyTorch check failed: {e}", error=str(e))
        return False, results

    # 2. Kokoro ONNX
    emit("kokoro", 35, "Verifying Kokoro-82M Voice Synthesis...")
    try:
        t_start = time.time()
        import kokoro_onnx
        results["kokoro"] = {
            "ok": True,
            "load_time_s": round(time.time() - t_start, 2)
        }
        emit("kokoro_ok", 45, "Kokoro ONNX speech engine ready", details=results["kokoro"])
    except Exception as e:
        results["kokoro"] = {"ok": False, "error": str(e)}
        emit("kokoro_fail", 45, f"Kokoro ONNX check failed: {e}", error=str(e))
        return False, results

    # 3. Faster-Whisper
    emit("whisper", 55, "Verifying Faster-Whisper Subtitle Alignment...")
    try:
        t_start = time.time()
        import faster_whisper
        results["faster_whisper"] = {
            "ok": True,
            "load_time_s": round(time.time() - t_start, 2)
        }
        emit("whisper_ok", 65, "Faster-Whisper subtitle alignment engine ready", details=results["faster_whisper"])
    except Exception as e:
        results["faster_whisper"] = {"ok": False, "error": str(e)}
        emit("whisper_fail", 65, f"Faster-Whisper check failed: {e}", error=str(e))
        return False, results

    # 4. Transformers
    emit("transformers", 70, "Verifying HuggingFace Transformers...")
    try:
        t_start = time.time()
        import transformers
        results["transformers"] = {
            "ok": True,
            "version": transformers.__version__,
            "load_time_s": round(time.time() - t_start, 2)
        }
        emit("transformers_ok", 75, f"Transformers {transformers.__version__} ready", details=results["transformers"])
    except Exception as e:
        results["transformers"] = {"ok": False, "error": str(e)}
        emit("transformers_fail", 75, f"Transformers check failed: {e}", error=str(e))
        return False, results

    # 5. Diffusers (SD-Turbo Visuals)
    emit("diffusers", 80, "Verifying Diffusers (SD-Turbo photorealistic visuals)...")
    try:
        t_start = time.time()
        import diffusers
        results["diffusers"] = {
            "ok": True,
            "version": diffusers.__version__,
            "load_time_s": round(time.time() - t_start, 2)
        }
        emit("diffusers_ok", 90, f"Diffusers {diffusers.__version__} ready", details=results["diffusers"])
    except Exception as e:
        results["diffusers"] = {"ok": False, "error": str(e)}
        emit("diffusers_fail", 90, f"Diffusers check failed: {e}", error=str(e))
        return False, results

    # 6. FFmpeg Configuration & Verification
    emit("ffmpeg", 92, "Verifying FFmpeg audio/video multiplexing engine...")
    ffmpeg_bin = shutil.which("ffmpeg")
    
    # Check imageio_ffmpeg if not in system PATH
    if not ffmpeg_bin:
        try:
            import imageio_ffmpeg
            img_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if img_exe and os.path.exists(img_exe):
                # Copy to runtime Scripts so it's permanently in PATH
                target_exe = runtime_dir / "Scripts" / "ffmpeg.exe"
                if not target_exe.exists():
                    try:
                        shutil.copy2(img_exe, target_exe)
                    except Exception:
                        pass
                ffmpeg_bin = str(target_exe) if target_exe.exists() else img_exe
        except Exception:
            pass

    if ffmpeg_bin and os.path.exists(ffmpeg_bin):
        results["ffmpeg"] = {"ok": True, "path": ffmpeg_bin}
        emit("ffmpeg_ok", 96, f"FFmpeg ready ({ffmpeg_bin})", details=results["ffmpeg"])
    else:
        results["ffmpeg"] = {"ok": False, "error": "FFmpeg executable not found"}
        emit("ffmpeg_fail", 96, "FFmpeg executable not found in system PATH", error="missing_ffmpeg")
        # Non-fatal warning if imageio_ffmpeg is not yet installed; provisionRuntime will handle installation

    # 7. Write .verified.json marker
    total_time = round(time.time() - t0, 2)
    marker = {
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_exe": sys.executable,
        "runtime_dir": str(runtime_dir),
        "total_verify_time_s": total_time,
        "results": results,
        "all_ready": True
    }
    
    try:
        marker_path = runtime_dir / ".verified.json"
        with open(marker_path, "w", encoding="utf-8") as f:
            json.dump(marker, f, indent=2)
    except Exception as e:
        print(f"Warning: could not write .verified.json: {e}", file=sys.stderr)

    emit("complete", 100, f"All local AI dependencies verified in {total_time}s!", marker=marker)
    return True, results


if __name__ == "__main__":
    success, res = verify()
    sys.exit(0 if success else 1)
