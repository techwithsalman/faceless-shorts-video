# Beyond History / Faceless Shorts AI Engine — GitHub Audit & Office PC Setup Report

**Date:** November 15, 2026  
**Local Project Path:** `C:\Users\Abdulwahab\faceless-shorts\`  
**Target Environment:** Office PC (Windows 10/11) Transfer for Monday  
**GitHub Repository:** [https://github.com/techwithsalman/faceless-shorts-video.git](https://github.com/techwithsalman/faceless-shorts-video.git)  
**Target Branch:** `main`  

---

## 1. GitHub Repository Audit Results

### A. Remote Repository Integration
- **Account:** `techwithsalman` (authenticated via GitHub CLI).
- **Target Repository:** `techwithsalman/faceless-shorts-video` (`https://github.com/techwithsalman/faceless-shorts-video.git`).
- **Remote Commit History Preserved:** The existing initial remote commit `fc55e76` (*"Initial commit"* by Salman Khan) is preserved as the base commit of the repository history.
- **Integration Strategy:** Fast-forward rebase integration. No force-pushing (`--force`) was used; zero remote history was overwritten.
- **Unrelated Repositories:** Confirmed untouched. All PostNexa repositories (`Postnexaapp`, `postnexa-website`) remain completely isolated.

### B. Local Git State
- **Branch:** `main` (synchronized with `origin/main`).
- **Commit History:**
  1. `fc55e76` — *Initial commit* (remote origin base).
  2. `5ce1afa` — *feat: Beyond History / Faceless Shorts AI Engine with office PC portability*.
  3. `9f41b2e` — *docs: finalize GitHub push audit and office PC setup report*.

---

## 2. Security Audit & Large File Protection

A comprehensive scan was conducted across the entire project before staging and committing:

| Check Category | Scan Result | Action Taken |
|---|---|---|
| **API Keys, Secrets, Passwords** | **0 Found** | Clean. Verified 100% offline local engine. |
| **.env Files & Credentials** | **0 Found** | Provided safe `.env.example` template without secrets. |
| **Generated MP4 Videos** | **15 Files (~400+ MB)** | **100% EXCLUDED** via `.gitignore` (`*.mp4`, `renders/`). |
| **Waveform Narration / Mixes** | **14 Files (~90 MB)** | **100% EXCLUDED** via `.gitignore` (`*.wav`, `data/*.wav`). |
| **Model Weights & Checkpoints** | **0 in repo (reside on D:)** | **100% EXCLUDED** (`*.onnx`, `*.bin`, `*.pt`, `cache/`). |
| **Virtual Environments** | **0 in repo (in ~/.faceless-shorts)**| **100% EXCLUDED** (`venv/`, `.venv/`). |
| **PostNexa References** | **0 Found** | Zero contamination from other projects. |

---

## 3. Files Included vs. Intentionally Excluded

### Included in Repository (Total: 664 files, ~72.4 MB):
- **Core Engine Scripts (`scripts/`):**
  - `produce_history.py` & `produce_history.ps1`: End-to-end historical documentary pipeline.
  - `voice.py`: Kokoro-82M ONNX offline speech synthesis.
  - `words.py`: Faster-Whisper word boundary synchronization.
  - `local_image.py`: Local `sd-turbo` image generation with CPU/CUDA detection.
  - `depth_estimator.py`: Monocular depth estimation for 2.5D WebGL parallax.
  - `setup_office_pc.ps1`: Automated hardware detection and dependency installer.
  - `new_video.ps1`, `new_video.sh`, `setup.sh`, `selftest.sh`, `py.ps1`.
- **Style Templates & Renders Engine (`styles/`):**
  - `beyond-history/`: 2.5D Depth-Displaced Parallax shaders, Three.js modules, typography, mix scripts.
  - `deep-dive/`, `night-file/`, `inside-out/`, `stick-story/`, `paper-atlas/`, `tall-tale/`: Procedural 3D/2D animation engines.
- **Batch 01 Documentary Packages (`beyond-history-batch-01/`):**
  - All 10 topic folders (01 through 10) tracking scripts (`script.json`, `data/script.json`), cues, word timestamps (`data/words.json`), scene composition code (`src/shots.js`), individual production reports, and lightweight visual contact sheets (`review/*-contact.jpg`).
- **Configuration & Documentation:**
  - `README.md`: Comprehensive engine architecture and office setup documentation.
  - `setup_office_pc.ps1`: Root installer script.
  - `requirements.txt`: Python package manifest.
  - `.env.example`: Non-secret environment template.
  - `.gitignore`: Multi-tier exclusion rules.
  - `SKILL.md`: Antigravity / Claude Agentic skill definition.
  - `AUDIT_AND_IMPROVEMENT_PLAN.md`: Full architectural improvement roadmap.
  - `GITHUB_PUSH_AND_OFFICE_SETUP_REPORT.md`: This report.

### Intentionally Excluded (Preserved on Local Disk):
- All rendered video MP4s in `beyond-history-batch-01/*/renders/*.mp4`, `marcus-aurelius-battlefield/renders/*.mp4`, `beyond-history-test/renders/*.mp4`, `one-dollar-bank/renders/*.mp4`.
- All heavy audio renders in `*/data/narration.wav` and `*/data/mix.wav`.
- Model cache directory `D:\faceless-shorts-ai\cache\` (~4.2 GB of SD-Turbo and Depth-Anything weights).
- Kokoro voice model directory `C:\Users\Abdulwahab\.faceless-shorts\kokoro\` (~340 MB).
- Python virtual environment `C:\Users\Abdulwahab\.faceless-shorts\venv\` (~5.8 GB).
- Temporary scratch generation scripts in `.gemini\antigravity\brain\...\scratch\`.

---

## 4. Office PC Setup Instructions (Monday Morning)

### Step 1: Clone Repository on Office PC
Open PowerShell (or Git Bash) on the office PC:
```powershell
cd C:\Users\<YourOfficeUsername>
git clone https://github.com/techwithsalman/faceless-shorts-video.git faceless-shorts
cd faceless-shorts
```

### Step 2: Run Automated Setup
Run the included setup script:
```powershell
powershell -ExecutionPolicy Bypass -File setup_office_pc.ps1
```
The script will automatically:
1. Detect CPU, RAM, and GPU (NVIDIA CUDA or CPU fallback).
2. Install Python 3.11, Node.js LTS, and FFmpeg via WinGet if missing.
3. Determine optimal model cache location (uses `D:\faceless-shorts-ai\cache` if drive D: exists, otherwise falls back to `%USERPROFILE%\.faceless-shorts\cache`).
4. Create the isolated Python virtual environment (`~/.faceless-shorts/venv`).
5. Install PyTorch (CUDA cu121 if NVIDIA GPU detected, otherwise CPU-optimized) and dependencies from `requirements.txt`.
6. Download the Kokoro-82M ONNX speech weights (~340 MB) locally.

### Step 3: Test Production
Produce a test documentary to verify full end-to-end operation on the office PC:
```powershell
$venvPy = "$HOME\.faceless-shorts\venv\Scripts\python.exe"
& $venvPy scripts/produce_history.py --project "beyond-history-test"
```

---

## 5. Remaining Manual Steps on Office PC

1. **Verify GPU drivers:** If your office PC has an NVIDIA GPU, ensure NVIDIA GeForce Game Ready or Studio Drivers are up to date so PyTorch can utilize CUDA.
2. **First Run Model Initialization:** On first generation, `sd-turbo` and `depth-anything-small-hf` will download once into your configured cache directory (~4.2 GB).
3. **No API keys or logins required:** The entire engine runs 100% locally with zero paid services or subscriptions.
