# AI Long Video Clipper — Production Build & Verification Report

**Build Date:** November 18, 2026  
**Product Name:** AI Long Video Clipper  
**Target Platform:** Windows 10 / Windows 11 (64-bit x64)  
**Author / Organization:** Beyond History AI Studios  
**License:** Proprietary  

---

## 1. Executive Summary
The AI Long Video Clipper module has been packaged into a Windows desktop application. The software is distributed as both a production NSIS Installer (`AI Long Video Clipper-Setup.exe`) and a standalone Portable Executable (`AI Long Video Clipper-Portable.exe`).

The desktop client integrates an Electron UI with a multithreaded Python backend leveraging Faster-Whisper, PyTorch CUDA acceleration, and FFmpeg.

---

## 2. Binary Artifacts

| Binary Artifact | Target | Size (Bytes) | Size (MB) | Location |
| :--- | :--- | :--- | :--- | :--- |
| **`AI Long Video Clipper-Setup.exe`** | NSIS Installer (x64) | 87,403,803 | 83.35 MB | `desktop-app/dist/AI Long Video Clipper-Setup.exe` |
| **`AI Long Video Clipper-Portable.exe`** | Portable Single EXE (x64) | 79,921,737 | 76.22 MB | `desktop-app/dist/AI Long Video Clipper-Portable.exe` |
| **`AI Long Video Clipper.exe`** | Unpacked Executable | 188,784,128 | 180.04 MB | `desktop-app/dist/win-unpacked/AI Long Video Clipper.exe` |

### Package Characteristics
- **Installer Framework:** NSIS 3.0.4.1 (64-bit)
- **Electron Version:** 33.4.11
- **Node.js:** v24.18.0 / NPM 11.16.0
- **Asar Package:** `app.asar` (87,889 bytes)
- **Extra Resources:** Full backend scripts (`clipper_server.py`, `clipper_engine.py`, `clipper.py`) bundled in `resources/scripts/`
- **Application Icon:** Multi-resolution high-DPI custom gold film-strip icon (`assets/icon.ico`, `assets/icon.png`)

---

## 3. Engine Audit & Quality Verification

### A. Live Video Clipping Test (Batch-005)
Prior to packaging, the clipping engine was verified using a CLI test on `AI-Video-Clips/uploads/Ciraut_Video_02.mp4`:
- **Command:** `python scripts/clipper.py -i AI-Video-Clips/uploads/Ciraut_Video_02.mp4 -d "30:1" -f vertical`
- **Output Batch:** `AI-Video-Clips/Batch-005`
- **Generated File:** `Ciraut_Video_02_clip01_27s_vertical.mp4` (5.14 MB)
- **Processing Time:** 29.03 seconds total
- **FFmpeg Stream Verification:**
  - Video: `H.264 (High Profile)`, `1080x1920` (9:16 vertical), `30.0 fps`
  - Audio: `AAC-LC stereo`, `48000 Hz`
  - Subtitles: Word-level speech timing with dynamic active-word yellow/gold highlights and black borders
  - Decode Check: `ffmpeg -v error -i ... -f null -` returned exit code `0` (Zero decode errors)

### B. Hardware Diagnostics & Self-Test Endpoint (`/api/test_engine`)
The backend self-test endpoint was tested via HTTP POST:
- **Status:** `200 OK`
- **FFmpeg:** Detected (`ffmpeg version 9.0.2-full_build-www.gyan.dev`)
- **PyTorch / CUDA:** Active (`NVIDIA GeForce GTX 1060 6GB`, CUDA 12.1)
- **Faster-Whisper:** Loaded from local model cache (`small.en`)
- **Engine Ready Flag:** `true`

---

## 4. Portability & Clean Machine Strategy

1. **Auto-Detection:**
   On launch, the desktop application probes for Python, FFmpeg, and the Faster-Whisper weights in system paths and application local paths.
2. **CPU Fallback Architecture:**
   If the target computer lacks an NVIDIA GPU, the engine automatically selects CPU Int8 quantization for transcription and `libx264` software encoding.
3. **One-Click Bootstrapper:**
   Clean Windows PCs can execute `setup_clean_pc.bat` to automatically install all dependencies silently without administrative friction.
4. **First-Run Setup Wizard:**
   Built directly into the Electron GUI, allowing users to verify hardware, select model cache directories, download missing models, and trigger instant engine tests.

---

## 5. Non-Destructive Storage Audit
All previous production assets were audited and verified intact:
- Completed batches: `Batch-001`, `Batch-002`, `Batch-003`, `Batch-004`, `Batch-005` preserved with manifests and clips.
- Uploaded source videos in `AI-Video-Clips/uploads/` preserved.
- Core Beyond History documentary engine files (`produce_history.py`, `words.py`, `voice.py`, `local_image.py`) untouched.
