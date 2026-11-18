# AI Long Video Clipper — System Requirements Specification

## 1. Overview
**AI Long Video Clipper** is a professional desktop workstation application for Windows 10/11 x64 designed to ingest long-form videos (15–60+ minutes), automatically extract viral/engaging moments using speech-to-text intelligence and audio-visual heuristics, and produce 1080x1920 vertical Shorts with burned word-level animated subtitles.

---

## 2. Hardware Requirements

### Minimum Configuration (CPU Inference & Software Encoding)
*Suitable for basic clip generation and lower-frequency workloads.*
- **Operating System:** Windows 10 (64-bit, Version 20H2 or later) / Windows 11 (64-bit)
- **Processor (CPU):** Intel Core i5 (6th Gen or newer) or AMD Ryzen 5 (2000 series or newer) (4 physical cores minimum)
- **Memory (RAM):** 16 GB DDR4
- **Graphics (GPU):** Integrated Intel UHD 630 / AMD Radeon Graphics (runs in CPU Int8 quantization mode)
- **Storage:** 10 GB free disk space (NVMe or SATA SSD recommended for source video IO)
- **Display Resolution:** 1360 x 768 minimum display resolution

### Recommended Configuration (NVIDIA CUDA Acceleration)
*Tested and benchmarked on Beyond History Production Workstations.*
- **Operating System:** Windows 10 / 11 64-bit (latest build)
- **Processor (CPU):** Intel Core i7-7700 (8 threads) / AMD Ryzen 7 3700X or higher
- **Memory (RAM):** 32 GB DDR4
- **Graphics (GPU):** NVIDIA GeForce GTX 1060 6GB, RTX 2060, RTX 3060, RTX 4060 or higher (CUDA 11.8 / 12.x compatible)
- **Dedicated VRAM:** 6 GB minimum dedicated GDDR5/GDDR6 VRAM
- **Storage:** 50+ GB available NVMe M.2 SSD space for video caching, whisper weights, and high-bitrate MP4 output
- **Display Resolution:** 1920 x 1080 (Full HD) or higher

---

## 3. Software & Runtime Dependencies

| Component | Minimum Version | Provided / Managed By | Purpose |
| :--- | :--- | :--- | :--- |
| **Electron Runtime** | v33.4.11 | Bundled in Installer & Portable EXE | Hardware-accelerated luxury Studio UI, native window controls, and IPC bridge |
| **Python** | 3.10 – 3.12 (64-bit) | Local Venv / Auto-Bootstrapper | Local AI backend and clip generation orchestrator |
| **FFmpeg** | 6.0+ (Tested on 9.0.2) | System PATH / Auto-Bootstrapper | Audio demuxing, video slicing, vertical 9:16 crop filter, subtitle burn-in |
| **Faster-Whisper** | 1.0.3+ | Python Environment | Local offline word-level speech transcription & timestamping |
| **PyTorch** | 2.5.1+cu121 | Python Environment | CUDA tensor compute engine for Whisper model |

---

## 4. Supported Input Formats
AI Long Video Clipper ingests standard video containers and codecs:
- **Containers:** `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`
- **Video Codecs:** H.264 (AVC), H.265 (HEVC), VP9, ProRes
- **Audio Codecs:** AAC, MP3, Opus, PCM 16/24-bit, AC3
- **Resolutions:** 720p, 1080p, 2K, 4K (3840x2160)
- **Aspect Ratios:** 16:9 widescreen, 4:3 traditional, 21:9 ultrawide

---

## 5. Output Specifications
All generated clips are standardized for immediate deployment to YouTube Shorts, Instagram Reels, and TikTok:
- **Resolution:** 1080 x 1920 pixels (9:16 vertical aspect ratio)
- **Framerate:** 30.0 fps constant framerate (CFR)
- **Video Codec:** H.264 / AVC (High Profile, Level 4.2)
- **Pixel Format:** YUV420p (broadest mobile and web compatibility)
- **Rate Control:** Constant Rate Factor (CRF 20, fast preset)
- **Audio Codec:** AAC-LC (Stereo, 192 kbps, 48 kHz)
- **Subtitles:** Burned hard subtitles with dynamic gold active word highlight and bottom safety margin padding.
