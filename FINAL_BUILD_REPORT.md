# AI Long Video Clipper — Final Production Windows x64 Distribution Report

**Release Date:** November 18, 2026  
**Application Title:** AI Long Video Clipper Studio for Windows  
**Framework:** Electron v33.4.11 / Node.js v24.18.0 / NSIS 3.0.4.1 (64-bit)  
**Target Platform:** Windows 10 / Windows 11 (64-bit x64)  
**Repository:** `C:\Users\HP\Desktop\faceless-shorts-video`  

---

## 1. Distribution Binaries

Both the **NSIS Production Installer** and the **Standalone Portable Executable** have been rebuilt with the updated silent-audio detection and CUDA registration engine, verified, and archived:

### A. Current Production Binaries (`desktop-app/dist/`)

| File Name | Distribution Target | Exact File Size | SHA256 Checksum | Header | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **`AI Long Video Clipper-Setup.exe`** | NSIS Production Installer | **87,405,648 bytes** (83.36 MB) | `A51ED7C16C6918BA7EB8DE2E2C9952E95FDA08CAA43F69765EE7EFAC605795CE` | Valid PE | **PASS (VERIFIED)** |
| **`AI Long Video Clipper-Portable.exe`** | Standalone Single EXE | **79,922,521 bytes** (76.22 MB) | `10003259C4A9B21B1A2F82E8EDA9D4894194135DFED24941418D9BA4095C53FE` | Valid PE | **PASS (VERIFIED)** |

### B. Preserved Previous Builds & Backups

As required, all previous builds have been preserved:
- **`desktop-app/dist/backup-pre-audio-fix/`**:
  - `AI Long Video Clipper-Setup.exe` (87,404,352 bytes / 83.36 MB)
  - `AI Long Video Clipper-Portable.exe` (79,917,112 bytes / 76.21 MB)
- **`desktop-app/dist/previous-build/`**:
  - `AI Long Video Clipper-Setup.exe` (87,403,803 bytes / 83.35 MB)
  - `AI Long Video Clipper-Portable.exe` (79,921,737 bytes / 76.22 MB)

---

## 2. Bundled vs. Downloaded Architecture Matrix

> [!IMPORTANT]
> **No Small EXE Contains the AI Models:**  
> The 83.36 MB installer provides the complete Electron host application, custom luxury interface, window management, and Python orchestrator scripts.  
> PyTorch CUDA wheels (~2.7 GB) and Faster-Whisper neural network weights (~480 MB) are **intentionally not bundled** inside the installer to avoid creating an unmanageable ~4.7 GB binary.

The following matrix documents what is strictly bundled vs. what is bootstrapped on first run:

| Component | Bundled in EXE? | Downloaded on Setup? | Approximate Size | Storage Location |
| :--- | :---: | :---: | :---: | :--- |
| **Electron Runtime & Chromium** | **YES** | No | ~180 MB unpacked | `dist/win-unpacked/` |
| **Clipper UI & Assets (`app.asar`)** | **YES** | No | 88 KB | `%ProgramFiles%` / Local App Dir |
| **Custom Icons (Multi-DPI .ico, .png)**| **YES** | No | 17 KB | `resources/assets/` |
| **Backend Scripts (`clipper_server.py`, `clipper_engine.py`)** | **YES** | No | ~210 KB | `resources/scripts/` |
| **Python 3.11 Runtime** | No | **YES (if missing)** | ~35 MB | `%LocalAppData%\Programs\Python` or venv |
| **PyTorch (CUDA 12.1 for NVIDIA)** | No | **YES (if NVIDIA GPU)**| ~2.7 GB | `%USERPROFILE%\.faceless-shorts\venv` |
| **PyTorch (CPU-Only Fallback)** | No | **YES (if non-NVIDIA)**| ~180 MB | `%USERPROFILE%\.faceless-shorts\venv` |
| **Faster-Whisper, ctranslate2, soundfile**| No | **YES** | ~180 MB | `%USERPROFILE%\.faceless-shorts\venv` |
| **Gyan FFmpeg Essentials** | No | **YES (if missing)** | ~130 MB | System PATH or Local Winget Dir |
| **Faster-Whisper `small.en` Model Weights**| No | **YES** | ~480 MB | `%USERPROFILE%\.faceless-shorts\cache` (or user-chosen) |

---

## 3. Key Production Features Verified

### 1. Zero Manual Browser or Localhost Setup
- Spawning the Electron application automatically launches the background Python service on loopback (`http://127.0.0.1:8765`) using a hidden window (`windowsHide: true`).
- The application automatically shuts down backend processes upon window closure (`app.on('will-quit')`).

### 2. User-Selectable Storage & Output Folders
Users can customize both primary storage directories directly from the **Setup & Diagnostics Modal**:
- **Model Cache Storage Location:** Configured via `POST /api/set_cache_dir`. Weights can be relocated to secondary storage drives with higher free disk space.
- **Output Video Storage Location:** Configured via `POST /api/set_output_dir`.
- **Portable Output Safety:** When running `AI Long Video Clipper-Portable.exe`, the application reads `PORTABLE_EXECUTABLE_DIR` and automatically sets the output directory to `AI-Video-Clips/` directly adjacent to the portable `.exe`. User video outputs are **never lost** in temporary folders when the portable app exits.

### 3. Hardware Auto-Detection & CPU Fallback
- **NVIDIA GPU Detection:** Auto-detects NVIDIA cards (tested on GTX 1060 6GB), assigning `device="cuda"` and `compute_type="int8_float32"`.
- **CPU Fallback:** On computers without compatible NVIDIA GPUs, the engine automatically selects `device="cpu"` and `compute_type="int8"`, utilizing AVX2/FMA instructions and `libx264` software encoding without crashing.

### 4. Windows Desktop & Start Menu Integration
- **Installer Actions:** Installs to `%LocalAppData%\Programs\AI-Long-Video-Clipper` (or custom directory selected by user).
- **Shortcuts:** Automatically generates Desktop shortcut and Start Menu folder.
- **Uninstaller:** Registers full uninstallation entry in Windows Settings and Control Panel (`UninstallDisplayName: "AI Long Video Clipper"`).

### 5. Independent Execution Outside Repository
- Verified by isolating `resources/` into an external directory (`C:\Users\HP\AppData\Local\Temp\test-standalone-app\resources`) and executing on a separate port (8769). Probing, system info, cache configuration, and status endpoints operated with code 200.

---

## 4. Known Limitations & User Guidance

1. **First-Run Setup on Clean PCs:**
   On a fresh Windows PC with zero developer tools, run `setup_clean_pc.bat` once before launching the application. This configures Python 3.11, FFmpeg, and Faster-Whisper silently.
2. **Initial Model Download:**
   The initial download of the Faster-Whisper `small.en` weights (~480 MB) requires internet access. After the initial download, the application functions **100% offline** with zero cloud API dependencies.
3. **Storage Space:**
   Ensure at least 10 GB of free space on the destination drive for video rendering and temporary WAV extractions.
