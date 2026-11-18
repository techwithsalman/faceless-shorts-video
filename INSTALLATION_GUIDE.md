# AI Long Video Clipper — Installation & Deployment Guide

## 1. Introduction
This guide describes how to install and run **AI Long Video Clipper** on any Windows 10/11 64-bit computer, including fresh/clean systems without pre-installed developer tools.

Two distribution packages are provided in the `desktop-app/dist/` directory:
1. **`AI Long Video Clipper-Setup.exe`** (83.36 MB) — Full Windows installer with standard installation wizard, Start Menu shortcuts, Desktop shortcut, and uninstaller support.
2. **`AI Long Video Clipper-Portable.exe`** (76.21 MB) — Standalone portable executable requiring no administrator privileges or file installation.

---

## 2. Installation on an Existing Machine (Developer or Office PC)
If the machine already has Python 3.10+, FFmpeg, and Faster-Whisper configured (such as the Beyond History production workstation):

1. Double-click `AI Long Video Clipper-Setup.exe`.
2. Follow the setup wizard to choose your preferred installation directory (Default: `%LocalAppData%\Programs\AI-Long-Video-Clipper`).
3. Click **Install**.
4. Once installation completes, check **Launch AI Long Video Clipper** and click **Finish**.
5. The application will automatically detect your local GPU (`NVIDIA GeForce GTX 1060 6GB`), verify FFmpeg in PATH, and load the pre-cached Faster-Whisper model.
6. The status indicator will turn green: **CUDA Active**.

---

## 3. Installation on a Fresh / Clean Windows PC (Zero Developer Tools)
> [!IMPORTANT]
> A fresh Windows 10/11 x64 PC has **no Python runtime, no PyTorch, and no FFmpeg**.  
> The 83.36 MB installer provides the complete Electron host application, custom luxury interface, window management, and Python orchestrator scripts.  
> PyTorch with CUDA 12.1 (~2.7 GB) and Faster-Whisper neural network weights (~480 MB) are **intentionally not bundled** inside the installer to avoid creating an unmanageable ~4.7 GB binary.

### Method A: Automated One-Click Bootstrapper (Recommended)
1. Copy or clone the project folder to the destination computer.
2. Right-click `setup_clean_pc.bat` and select **Run as Administrator** (or run normally).
3. The script will automatically:
   - Detect system hardware and available GPUs.
   - Install Python 3.11 silently via Windows Package Manager (`winget`) or initialize a standalone venv.
   - Download and install official Gyandev FFmpeg essentials.
   - Install required PyTorch runtime (CUDA 12.1 for NVIDIA GPUs, or CPU Int8 optimized wheels for Intel/AMD).
   - Pre-cache Faster-Whisper `small.en` weights (~480 MB).
4. Run `AI Long Video Clipper-Setup.exe`.

### Method B: In-App First-Run Setup Wizard
If you launch `AI Long Video Clipper` directly on a machine where components are missing:
1. The app detects missing items and opens the **First-Run Setup & Diagnostics Wizard**.
2. **Faster-Whisper Model:** If the model weights are missing, click **Download Model (~480 MB)**. The app downloads the official weights into `%USERPROFILE%\.faceless-shorts\cache`.
3. **Hardware Acceleration:**
   - If an NVIDIA GPU with CUDA is detected, hardware acceleration is engaged automatically (`device="cuda"`).
   - If no NVIDIA card is present, the app gracefully engages **CPU Fallback Mode** (`compute_type="int8"` and `libx264` fast encoding), operating without crashes.
4. **Diagnostic Verification:** Click **⚡ Test Engine** to run an automated check verifying FFmpeg execution, Faster-Whisper model loading, and speech inference.

---

## 4. User-Selectable Storage & Output Folders
Users can customize storage locations directly from the **Setup & Diagnostics Modal**:
- **Model Cache Storage Location:** Click **Change Folder** next to Model Cache to relocate Whisper model weights to any internal or external drive with ample free space.
- **Output Video Storage Location:** Click **Change Folder** next to Output Video Storage to save rendered clips to custom project directories.

---

## 5. Portable Edition Usage & Output Safety
- Double-click `AI Long Video Clipper-Portable.exe` to run immediately without installation.
- **Output Safety Guarantee:** The portable edition automatically outputs rendered clips to `AI-Video-Clips/` directly adjacent to the portable `.exe` (via `PORTABLE_EXECUTABLE_DIR`). Generated videos are **never lost** when the portable sandbox closes.

---

## 6. Uninstallation
To remove the application:
1. Open Windows **Settings** > **Apps** > **Installed apps**.
2. Search for **AI Long Video Clipper**.
3. Click **Uninstall** and confirm.
4. Shortcuts, app binaries, and cached assets will be cleanly removed.
*(Note: Generated video batches inside `AI-Video-Clips/` and original uploads are never deleted during uninstall to protect your work).*
