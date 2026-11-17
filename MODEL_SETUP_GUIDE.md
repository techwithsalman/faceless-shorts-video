# Prompt2Video AI — Local AI Model Suite & Offline Setup

Prompt2Video AI operates **100% offline** on consumer hardware. It requires **$0.00** in API fees, zero subscriptions, and no active internet connection once the open-weight model weights are cached.

---

## 1. Model Architecture Overview

```
                                [ User Prompt ]
                                       │
                                       ▼
                   ┌───────────────────────────────────────┐
                   │ Stage 1: Script & Scene Planning      │
                   │ Model: Qwen2.5-0.5B-Instruct          │
                   │ Size: ~600 MB (float32 / int8 CPU)    │
                   └──────────────────┬────────────────────┘
                                      │
                   ┌──────────────────┴────────────────────┐
                   ▼                                       ▼
┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
│ Stage 2: Neural Voice Synthesis     │ │ Stage 4: Photorealistic Visuals     │
│ Model: Kokoro-82M (ONNX Runtime)    │ │ Model: SD-Turbo (Stability AI)      │
│ Size: ~340 MB                       │ │ Size: ~2.1 GB (Diffusers 1-step)    │
└──────────────────┬──────────────────┘ └──────────────────┬──────────────────┘
                   │                                       │
                   ▼                                       ▼
┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
│ Stage 3: Word-Level Subtitles       │ │ Stage 5: 2.5D Volumetric Parallax   │
│ Model: Faster-Whisper (small.en)    │ │ Model: Depth-Anything-V2-Small      │
│ Size: ~140 MB (CTranslate2 int8)    │ │ Size: ~380 MB (ONNX / Torch)        │
└──────────────────┬──────────────────┘ └──────────────────┬──────────────────┘
                   │                                       │
                   └──────────────────┬────────────────────┘
                                      │
                                      ▼
                   ┌───────────────────────────────────────┐
                   │ Stage 6: Video Assembly & Mix         │
                   │ Engine: Headless CDP + Three.js +     │
                   │         Procedural Audio + FFmpeg     │
                   │ Output: 1080x1920 30FPS H.264 MP4     │
                   └───────────────────────────────────────┘
```

---

## 2. Model Specifications & Cache Locations

### 1. Script & Scene Planning (`local_llm.py`)
- **Model**: `Qwen/Qwen2.5-0.5B-Instruct`
- **Architecture**: Causal Language Model (0.5 Billion Parameters)
- **Disk Footprint**: ~600 MB
- **Inference**: PyTorch on CPU (AVX2 / FMA3)
- **Cache Path**: `D:\faceless-shorts-ai\cache\models--Qwen--Qwen2.5-0.5B-Instruct`

### 2. Neural Voiceover Synthesis (`voice.py`)
- **Model**: `Kokoro-82M v1.0`
- **Architecture**: StyleTTS 2 / ISTFTNet Text-to-Speech
- **Disk Footprint**: ~340 MB (`kokoro-v1.0.onnx` + `voices-v1.0.bin`)
- **Inference**: ONNX Runtime (CPU multi-threading)
- **Cache Path**: `C:\Users\<User>\.faceless-shorts\kokoro\`

### 3. Subtitle Timing & Word Alignment (`words.py`)
- **Model**: `faster-whisper-small.en`
- **Architecture**: CTranslate2 int8 quantized Whisper
- **Disk Footprint**: ~140 MB
- **Inference**: CTranslate2 CPU int8
- **Cache Path**: `D:\faceless-shorts-ai\cache\hub\models--Systran--faster-whisper-small.en`

### 4. Photorealistic Visual Generation (`local_image.py`)
- **Model**: `stabilityai/sd-turbo`
- **Architecture**: Adversarial Diffusion Distillation (ADD) — single-step latent diffusion
- **Disk Footprint**: ~2.1 GB
- **Inference**: Diffusers on CPU (attention slicing + memory efficient attention)
- **Resolution**: 512×512 native (scaled to 1080×1920 or 720×1280 with letterbox / aspect-fit)
- **Cache Path**: `D:\faceless-shorts-ai\cache\models--stabilityai--sd-turbo`

### 5. 2.5D Volumetric Depth Parallax (`depth_estimator.py`)
- **Model**: `LiheYoung/depth-anything-small-hf` / `Depth-Anything-V2-Small`
- **Architecture**: Vision Transformer monocular depth estimation
- **Disk Footprint**: ~380 MB
- **Inference**: PyTorch / ONNX CPU
- **Output**: 16-bit / 8-bit normalized grayscale depth map
- **Cache Path**: `D:\faceless-shorts-ai\cache\models--depth-anything--Depth-Anything-V2-Small-hf`

---

## 3. Pre-loading Models on a New Machine (e.g. Office PC)

To transfer your entire setup from your current laptop to your office PC without re-downloading anything:

1. Copy the `D:\faceless-shorts-ai\cache` folder to an external USB drive (total size: ~4.5 GB).
2. On the office PC, place the folder at `D:\faceless-shorts-ai\cache` (or `%USERPROFILE%\.faceless-shorts\cache`).
3. Set the environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("HF_HOME", "D:\faceless-shorts-ai\cache", "User")
   ```
4. Copy `C:\Users\<User>\.faceless-shorts\kokoro` to `%USERPROFILE%\.faceless-shorts\kokoro`.
5. Launch `Prompt2Video-AI-Setup.exe` and begin generating videos immediately!
