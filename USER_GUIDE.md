# AI Long Video Clipper — User & Production Guide

## 1. Studio Interface Overview
The **AI Long Video Clipper Studio** features a modern dark luxury interface designed for high-throughput video editing:
- **Header:** Displays live hardware status (`NVIDIA GTX 1060 CUDA Active` or `CPU Fallback`), active backend port, and shortcut buttons (**System Diagnostics**, **Batch History**, and **Output Folder**).
- **Video Staging (Left Column):** Upload dropzone supporting multiple file selection, drag-and-drop, individual video cards with live file size and duration preview, and a **Library Browser** to reuse previously uploaded source videos.
- **Production Pipeline (Right Column):** Duration breakdown controls (30s, 45s, 60s), aspect ratio selector, subtitle styling preview, one-click execution button, real-time stage progress bar, and streaming system logs.
- **Batch Output Gallery:** Displays generated video clips for immediate playback, right-click file operations, and one-click opening in Windows File Explorer.

---

## 2. Step-by-Step Workflow

### Step 1: Add Source Videos
1. Click the **+ Add Videos** button or drag and drop 1 to 5 long-form video files into the upload box.
2. Supported formats: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`.
3. The application displays a card for each video showing filename, resolution, format, and file size.
4. If you have previously uploaded videos, click **Show Library** to inspect existing source files and add them to your current batch with a single click.

### Step 2: Configure Clip Durations & Targets
Specify how many clips of each duration you want to generate:
- **30-second clips:** Fast-paced viral hooks and dynamic summaries.
- **45-second clips:** Balanced storytelling clips with setup, narrative, and climax.
- **60-second clips:** Deep-dive clips with complete contextual explanations and conclusions.
*(Example: For 3 videos targeting ~54 clips total, set 10 clips at 45s and 8 clips at 60s per video).*

### Step 3: Choose Framing and Subtitles
- **Framing Mode:**
  - `Vertical (9:16)` — Center-crop optimized for Shorts, Reels, TikTok (1080x1920).
  - `Horizontal (16:9)` — Widescreen original framing (1920x1080).
  - `Square (1:1)` — Square social post format (1080x1080).
- **Subtitles:** Automatically generated with word-level speech synchronization, yellow/gold dynamic highlighting on currently spoken words, high-contrast black outline, and vertical positioning configured above UI navigation buttons.

### Step 4: Start Processing
1. Click **Start AI Long Video Clipper**.
2. The UI switches to active processing state:
   - Overall progress bar tracks percentage completion across all videos.
   - Stage indicators display: *Extracting Audio* ➔ *Transcribing Speech* ➔ *Analyzing Key Moments* ➔ *Rendering 1080x1920 Clips*.
   - Live logs display timecode cuts, selected moment scores, and encoding details.

### Step 5: Review & Export Clips
1. When all clips finish rendering, the **Batch Completed Successfully** banner appears.
2. The **Batch Output Gallery** lists every produced video clip with video player preview and duration.
3. Click **Open in Explorer** to immediately access the output folder on your disk.

---

## 3. Safe Multi-Batch Management
The AI Long Video Clipper is built with strict non-destructive storage guarantees:
- **Start New Batch:** Click the gold **Start New Batch** button after a batch completes. This resets the UI state, generates a fresh Job ID, and increments the batch directory (e.g. `Batch-006`).
- **Data Protection:** Previous batch folders (`Batch-001` through `Batch-005`), completed clips, and uploaded source videos are **never deleted or overwritten**.
- **Batch History:** Click the **Batch History** button in the header at any time to review past batches, clip counts, duration breakdowns, and open any historical batch folder directly in Windows Explorer.
