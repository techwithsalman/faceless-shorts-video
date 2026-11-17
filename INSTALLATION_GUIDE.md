# Prompt2Video AI — User Installation & Quickstart Guide

> **Your Prompt. Your Video. Powered by Local AI.**  
> Create complete, synchronized, narrated short-form videos completely offline on your Windows PC with zero cloud APIs, subscriptions, or credit cards.

---

## 1. System Requirements

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit, Build 19041+) | Windows 11 (64-bit) |
| **Processor (CPU)** | Intel Core i5 / AMD Ryzen 5 (AVX2 support) | Intel Core i7 / AMD Ryzen 7+ |
| **System Memory (RAM)** | 8 GB | 16 GB or higher |
| **Graphics (GPU)** | Intel HD 620 / Integrated (CPU inference supported) | NVIDIA RTX 3060 / 4060+ (CUDA acceleration) |
| **Storage Space** | 10 GB free space (SSD recommended) | 20 GB free space on D: drive or fast NVMe |

---

## 2. Installation via Windows Installer

1. Download **`Prompt2Video-AI-Setup.exe`**.
2. Double-click the installer to launch the Setup Wizard.
3. Choose your preferred installation folder (e.g., `C:\Program Files\Prompt2Video AI` or `D:\Prompt2Video AI`).
4. Select **Create Desktop Shortcut** and click **Install**.
5. Once installation finishes, check **Launch Prompt2Video AI** and click **Finish**.

---

## 3. First-Launch Setup Wizard

When you open Prompt2Video AI for the first time:

1. **Hardware Audit**: The application scans your CPU, RAM, and GPU to ensure optimal inference settings.
2. **Storage Selection**: Choose where generated videos and local model caches should be saved. If your C: drive has limited space, choose your secondary drive (e.g., `D:\faceless-shorts-ai\cache`).
3. **Local AI Verification**: The app confirms that the 5 required offline open-weight neural models are available:
   - **Kokoro-82M**: Neural text-to-speech engine.
   - **SD-Turbo**: Ultra-fast photorealistic visual generator.
   - **Depth-Anything V2**: 2.5D volumetric parallax depth estimator.
   - **Faster-Whisper**: Word-level subtitle alignment.
   - **Qwen2.5-0.5B-Instruct**: Script and scene planning model.

---

## 4. How to Generate Your First Video

1. In the **Create Video** tab, enter your video topic in the prompt box (e.g., *Why the Titanic really sank*).
2. Choose your preferred **Target Duration** (15s, 30s, 45s, or 60s).
3. Select your **Aspect Ratio**:
   - `9:16 Vertical` (Shorts, Reels, TikTok)
   - `16:9 Landscape` (YouTube, TV)
   - `1:1 Square` (Instagram Feed)
4. Choose an **AI Voice** (e.g., Adam for deep documentary narration).
5. Click **Generate Video (100% Offline AI)**.
6. The app switches automatically to the **Production Studio** tab:
   - Watch the 6-stage pipeline progress in real-time.
   - Preview generated scenes, narration text, and 2.5D depth maps as they appear.
7. When complete, preview your video in the built-in player or click **Show in Explorer** to export your MP4!
