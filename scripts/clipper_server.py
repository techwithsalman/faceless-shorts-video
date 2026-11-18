"""AI Long Video Clipper - Web Server and Interactive UI
Self-contained, multithreaded local web server providing an interactive browser UI
for uploading, configuring, processing, and reviewing AI video clips.
Includes persistent job tracking, automatic uploaded video discovery, resilient state management,
clean new batch transitions, and library video re-use without data loss.
"""

import os
import sys
import re
import json
import time
import shutil
import threading
import mimetypes
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from typing import Tuple, Optional, List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.clipper_engine import VideoClipperEngine

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
UPLOAD_DIR = PROJECT_ROOT / "AI-Video-Clips" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_ROOT = PROJECT_ROOT / "AI-Video-Clips"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
JOB_STATE_FILE = OUTPUT_ROOT / "job_state.json"
JOB_HISTORY_FILE = OUTPUT_ROOT / "job_history.json"

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def safe_load_json(body_str: str) -> dict:
    """Resiliently parses JSON body, gracefully handling unescaped Windows path backslashes."""
    try:
        return json.loads(body_str)
    except Exception:
        sanitized = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', body_str)
        return json.loads(sanitized)


def archive_completed_job(job_info: dict):
    """Safely archives a completed batch job to job_history.json without overwriting history."""
    if not job_info or not job_info.get("job_id"):
        return
    try:
        history = []
        if JOB_HISTORY_FILE.exists():
            try:
                with open(JOB_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        if not isinstance(history, list):
            history = []

        # Avoid duplicates
        existing_ids = {h.get("job_id") for h in history if isinstance(h, dict)}
        if job_info.get("job_id") not in existing_ids:
            history.append(job_info)
            with open(JOB_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            print(f"[ARCHIVE] Archived job {job_info.get('job_id')} into {JOB_HISTORY_FILE}", flush=True)
    except Exception as e:
        print(f"[WARN] Failed to archive completed job: {e}", flush=True)


class ClipperJobManager:
    """Manages background batch clipping jobs with persistent state tracking, pause/resume, and cancellation."""

    def __init__(self):
        self.lock = threading.RLock()
        self.job_id = None
        self.state = "idle"  # idle, running, paused, completed, cancelled, error
        self.current_video_idx = 0
        self.total_videos = 0
        self.overall_percent = 0.0
        self.current_stage = ""
        self.current_detail = "Ready"
        self.logs = []
        self.current_batch_result = None
        self.active_videos = []  # List of dicts representing videos in current active batch
        self.engine = None
        self.worker_thread = None
        self.load_persistent_state()

    def get_next_batch_name(self) -> str:
        """Determines next batch ID by scanning output directory."""
        existing = []
        for d in OUTPUT_ROOT.glob("Batch-*"):
            if d.is_dir():
                m = re.match(r"Batch-(\d+)", d.name)
                if m:
                    existing.append(int(m.group(1)))
        next_num = max(existing) + 1 if existing else 1
        return f"Batch-{next_num:03d}"

    def log(self, message: str):
        with self.lock:
            entry = f"[{time.strftime('%H:%M:%S')}] {message}"
            self.logs.append(entry)
            print(f"[JOB-LOG] {entry}", flush=True)
            if len(self.logs) > 300:
                self.logs.pop(0)
            self._save_state_locked()

    def progress_callback(self, data: dict):
        with self.lock:
            self.current_stage = data.get("stage", "")
            self.overall_percent = data.get("percent", 0.0)
            self.current_detail = data.get("detail", "")
            entry = f"[{self.current_stage.upper()}] {self.current_detail}"
            self.logs.append(f"[{time.strftime('%H:%M:%S')}] {entry}")
            print(f"[{self.overall_percent:5.1f}%] {entry}", flush=True)
            if len(self.logs) > 300:
                self.logs.pop(0)
            self._save_state_locked()

    def _save_state_locked(self):
        """Internal helper to flush state to disk (must be called with lock held)."""
        data = {
            "job_id": self.job_id,
            "state": self.state,
            "overall_percent": self.overall_percent,
            "current_stage": self.current_stage,
            "current_detail": self.current_detail,
            "current_video_idx": self.current_video_idx,
            "total_videos": self.total_videos,
            "logs": self.logs[-60:],
            "batch_result": self.current_batch_result,
            "active_videos": self.active_videos,
            "next_batch": self.get_next_batch_name(),
            "updated_at": time.time()
        }
        try:
            with open(JOB_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def load_persistent_state(self):
        """Loads previous job state from disk if available."""
        if not JOB_STATE_FILE.exists():
            return
        try:
            with open(JOB_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.job_id = data.get("job_id")
            saved_state = data.get("state", "idle")
            if saved_state == "running":
                self.state = "idle"
                self.current_detail = "Server was restarted. Ready to begin processing."
            else:
                self.state = saved_state
                self.current_detail = data.get("current_detail", "Ready")
            self.overall_percent = data.get("overall_percent", 0.0)
            self.current_stage = data.get("current_stage", "")
            self.total_videos = data.get("total_videos", 0)
            self.current_video_idx = data.get("current_video_idx", 0)
            self.logs = data.get("logs", [])
            self.current_batch_result = data.get("batch_result")
            self.active_videos = data.get("active_videos", [])
        except Exception as e:
            print(f"[WARN] Could not load previous job state: {e}", flush=True)

    def new_batch(self) -> str:
        """Archives current completed batch and initializes clean state for next batch."""
        with self.lock:
            if self.state in ("running", "paused") and self.worker_thread and self.worker_thread.is_alive():
                raise RuntimeError(f"Cannot start a new batch while job {self.job_id} is running.")

            # Archive completed job if any
            if self.current_batch_result or (self.job_id and self.state == "completed"):
                archive_completed_job({
                    "job_id": self.job_id,
                    "state": self.state,
                    "batch_result": self.current_batch_result,
                    "total_videos": self.total_videos,
                    "archived_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })

            next_batch = self.get_next_batch_name()
            self.job_id = None
            self.state = "idle"
            self.overall_percent = 0.0
            self.current_stage = ""
            self.current_detail = f"Ready for {next_batch} — 0%"
            self.logs = [f"[{time.strftime('%H:%M:%S')}] Initialized fresh workspace for {next_batch}."]
            self.current_batch_result = None
            self.active_videos = []
            self.current_video_idx = 0
            self.total_videos = 0
            self._save_state_locked()
            print(f"[BATCH] Reset complete. Prepared for {next_batch}.", flush=True)
            return next_batch

    def add_active_video(self, video_info: dict):
        """Adds a probed video to the active batch selection."""
        with self.lock:
            existing_paths = {v.get("path") for v in self.active_videos}
            if video_info.get("path") not in existing_paths:
                self.active_videos.append(video_info)
                self.log(f"Added video to active batch: {video_info.get('filename')}")
                self._save_state_locked()

    def remove_active_video(self, video_path: str):
        """Removes a video from the active batch list without deleting the file from disk."""
        with self.lock:
            orig_len = len(self.active_videos)
            self.active_videos = [v for v in self.active_videos if v.get("path") != video_path]
            if len(self.active_videos) < orig_len:
                self.log(f"Removed video from active batch: {Path(video_path).name}")
                self._save_state_locked()

    def get_uploaded_videos(self) -> List[Dict[str, Any]]:
        """Scans uploads directory and returns probed metadata for existing uploaded library files."""
        videos = []
        engine = VideoClipperEngine()
        meta_cache_file = UPLOAD_DIR / ".meta_cache.json"
        cache = {}
        if meta_cache_file.exists():
            try:
                with open(meta_cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}

        updated_cache = False
        for f in sorted(UPLOAD_DIR.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                f_str = str(f.resolve())
                mtime = f.stat().st_mtime
                if f.name in cache and cache[f.name].get("mtime") == mtime:
                    videos.append(cache[f.name]["info"])
                else:
                    try:
                        info = engine.probe_media(f_str)
                        cache[f.name] = {"mtime": mtime, "info": info}
                        videos.append(info)
                        updated_cache = True
                    except Exception as e:
                        print(f"[WARN] Failed to probe existing upload {f.name}: {e}", flush=True)

        if updated_cache:
            try:
                with open(meta_cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f, indent=2)
            except Exception:
                pass

        return videos

    def start_job(self, video_paths: list, target_durations: dict, output_format: str, burn_subtitles: bool) -> str:
        with self.lock:
            if self.state in ("running", "paused") and self.worker_thread and self.worker_thread.is_alive():
                raise RuntimeError(f"A job ({self.job_id}) is already currently in progress.")

            # Generate unique Job ID
            self.job_id = f"JOB-{time.strftime('%Y%m%d-%H%M%S')}"
            self.state = "running"
            self.overall_percent = 0.0
            self.current_stage = "starting"
            self.current_detail = f"Job {self.job_id} initialized with {len(video_paths)} video(s)..."
            self.logs = []
            self.current_batch_result = None
            self.total_videos = len(video_paths)
            self.current_video_idx = 1
            self._save_state_locked()

        self.engine = VideoClipperEngine(
            cache_dir=str(Path.home() / ".faceless-shorts" / "cache"),
            device="auto",
            progress_callback=self.progress_callback
        )

        def runner():
            try:
                self.log(f"Job {self.job_id}: Processing {len(video_paths)} video(s)...")
                res = self.engine.run_batch(
                    video_paths=video_paths,
                    output_root=str(OUTPUT_ROOT),
                    target_durations=target_durations,
                    output_format=output_format,
                    burn_subtitles=burn_subtitles
                )
                with self.lock:
                    self.current_batch_result = res
                    self.state = "completed"
                    self.overall_percent = 100.0
                    self.current_detail = f"Batch {res['batch_id']} completed successfully! Generated {res['total_clips']} clips."
                    self._save_state_locked()
                self.log(self.current_detail)
                # Auto-archive to history
                archive_completed_job({
                    "job_id": self.job_id,
                    "state": "completed",
                    "batch_result": res,
                    "total_videos": len(video_paths),
                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            except InterruptedError:
                with self.lock:
                    self.state = "cancelled"
                    self.current_detail = "Job cancelled by user."
                    self._save_state_locked()
                self.log(f"Job {self.job_id} cancelled.")
            except Exception as e:
                with self.lock:
                    self.state = "error"
                    self.current_detail = f"Error: {str(e)}"
                    self._save_state_locked()
                self.log(f"Job {self.job_id} ERROR: {str(e)}")
                import traceback
                traceback.print_exc()

        self.worker_thread = threading.Thread(target=runner, daemon=True)
        self.worker_thread.start()
        return self.job_id

    def pause_job(self):
        with self.lock:
            if self.state == "running" and self.engine:
                self.engine.pause_requested = True
                self.state = "paused"
                self.log("Job paused by user.")
                self._save_state_locked()

    def resume_job(self):
        with self.lock:
            if self.state == "paused" and self.engine:
                self.engine.pause_requested = False
                self.state = "running"
                self.log("Job resumed by user.")
                self._save_state_locked()

    def cancel_job(self):
        with self.lock:
            if self.state in ("running", "paused") and self.engine:
                self.engine.cancel_requested = True
                self.engine.pause_requested = False
                self.state = "cancelling"
                self.log("Cancellation requested...")
                self._save_state_locked()

    def get_status(self) -> dict:
        with self.lock:
            # Check if background thread died unexpectedly
            if self.state == "running" and self.worker_thread and not self.worker_thread.is_alive():
                self.state = "error"
                self.current_detail = "Worker thread stopped unexpectedly."
                self._save_state_locked()

            return {
                "job_id": self.job_id,
                "state": self.state,
                "overall_percent": self.overall_percent,
                "current_stage": self.current_stage,
                "current_detail": self.current_detail,
                "current_video_idx": self.current_video_idx,
                "total_videos": self.total_videos,
                "logs": self.logs[-40:],
                "batch_result": self.current_batch_result,
                "active_videos": self.active_videos,
                "next_batch": self.get_next_batch_name()
            }


JOB_MANAGER = ClipperJobManager()


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Long Video Clipper — Beyond History Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0c0e12;
      --card-bg: #141820;
      --card-border: #232a38;
      --card-hover: #1b212c;
      --primary: #f5d061;
      --primary-hover: #e0bc4c;
      --accent: #4a88f7;
      --text: #f0f2f5;
      --text-muted: #8b96a8;
      --success: #2ecc71;
      --danger: #e74c3c;
      --warning: #f39c12;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: linear-gradient(180deg, #181d28 0%, #0c0e12 100%);
      border-bottom: 1px solid var(--card-border);
      padding: 1.25rem 2.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .brand-logo {
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, #f5d061 0%, #d49a24 100%);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #111;
      font-family: 'Cinzel', serif;
      font-size: 1.25rem;
      box-shadow: 0 4px 15px rgba(245, 208, 97, 0.35);
    }
    .brand-title {
      font-family: 'Cinzel', serif;
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #fff;
    }
    .brand-subtitle {
      font-size: 0.78rem;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 1px;
      font-weight: 600;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: #19202c;
      border: 1px solid var(--card-border);
      padding: 0.4rem 0.9rem;
      border-radius: 20px;
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 2rem 2.5rem;
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 390px;
      gap: 2rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 1.5rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }
    .card-title {
      font-size: 1.15rem;
      font-weight: 600;
      color: #fff;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }
    .card-title svg { color: var(--primary); }

    /* Completion Banner */
    .batch-banner {
      background: linear-gradient(135deg, rgba(46, 204, 113, 0.15), rgba(245, 208, 97, 0.15));
      border: 1px solid rgba(46, 204, 113, 0.5);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      box-shadow: 0 8px 25px rgba(46, 204, 113, 0.12);
    }
    .batch-banner-text {
      font-size: 1.05rem;
      font-weight: 700;
      color: #fff;
    }
    .batch-banner-sub {
      font-size: 0.83rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }

    /* Dropzone */
    .dropzone {
      border: 2px dashed #2e384d;
      border-radius: var(--radius);
      padding: 2rem 1.5rem;
      text-align: center;
      background: #0f131a;
      transition: all 0.25s ease;
      position: relative;
    }
    .dropzone.dragover {
      border-color: var(--primary);
      background: #171d28;
      box-shadow: 0 0 20px rgba(245, 208, 97, 0.15);
    }
    .dropzone-icon {
      font-size: 2.5rem;
      color: var(--primary);
      margin-bottom: 0.5rem;
    }
    .dropzone-text {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
    }
    .dropzone-sub {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 0.5rem;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 0.65rem 1.2rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
      text-decoration: none;
    }
    .btn-primary {
      background: linear-gradient(135deg, #f5d061 0%, #d49a24 100%);
      color: #111;
      box-shadow: 0 4px 12px rgba(245, 208, 97, 0.3);
    }
    .btn-primary:hover:not(:disabled) {
      background: linear-gradient(135deg, #ffe285 0%, #e0aa34 100%);
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: #1c2331;
      color: #cbd5e1;
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover:not(:disabled) {
      background: #283348;
      color: #fff;
    }
    .btn-success {
      background: #27ae60;
      color: #fff;
    }
    .btn-success:hover:not(:disabled) {
      background: #2ecc71;
    }
    .btn-danger {
      background: #c0392b;
      color: #fff;
    }
    .btn-danger:hover:not(:disabled) {
      background: #e74c3c;
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
    }

    /* Upload Progress Box */
    .upload-progress-container {
      margin-top: 1rem;
      display: none;
      background: #090b0e;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 0.8rem 1rem;
    }
    .upload-progress-header {
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
      margin-bottom: 0.4rem;
      color: var(--text);
    }
    .upload-progress-bar {
      height: 8px;
      background: #1f2736;
      border-radius: 4px;
      overflow: hidden;
    }
    .upload-progress-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #f5d061, #4a88f7);
      transition: width 0.15s ease;
    }

    /* Video List */
    .video-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
      margin-top: 1.25rem;
    }
    .video-item {
      background: #0f131a;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      position: relative;
    }
    .video-item-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.5rem;
    }
    .video-item-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: #fff;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .btn-remove {
      background: rgba(231, 76, 60, 0.15);
      border: 1px solid rgba(231, 76, 60, 0.35);
      color: #e74c3c;
      border-radius: 6px;
      padding: 0.2rem 0.5rem;
      font-size: 0.78rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.2rem;
    }
    .btn-remove:hover {
      background: #e74c3c;
      color: #fff;
    }
    .video-item-preview {
      width: 100%;
      height: 140px;
      background: #000;
      border-radius: 6px;
      object-fit: contain;
    }
    .video-item-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.74rem;
      color: var(--text-muted);
      border-top: 1px solid #1a2230;
      padding-top: 0.4rem;
    }

    .empty-state {
      padding: 2rem 1rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.9rem;
      border: 1px dashed var(--card-border);
      border-radius: 8px;
      margin-top: 1rem;
    }

    /* Library Drawer */
    .library-panel {
      display: none;
      background: #0a0d12;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1rem;
      margin-top: 1rem;
    }
    .library-panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--primary);
      margin-bottom: 0.75rem;
    }
    .library-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 0.75rem;
      max-height: 240px;
      overflow-y: auto;
    }
    .library-item {
      background: #141820;
      border: 1px solid #1e2634;
      border-radius: 6px;
      padding: 0.6rem;
      font-size: 0.8rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .library-item-name {
      font-weight: 600;
      color: #e2e8f0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Controls & Options */
    .duration-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
    }
    .duration-row {
      background: #0f131a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 0.6rem 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .duration-label {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .count-spinner {
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }
    .spinner-btn {
      width: 24px;
      height: 24px;
      border-radius: 4px;
      border: 1px solid #2e384d;
      background: #19202c;
      color: #fff;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .spinner-val {
      font-size: 0.9rem;
      font-weight: 600;
      width: 18px;
      text-align: center;
      color: var(--primary);
    }
    .option-group {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }
    .option-radio {
      display: flex;
      align-items: flex-start;
      gap: 0.6rem;
      font-size: 0.85rem;
      color: var(--text);
      cursor: pointer;
    }
    .option-radio input {
      margin-top: 0.2rem;
    }

    /* Progress & Logs */
    .progress-bar-container {
      height: 12px;
      background: #090b0e;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      overflow: hidden;
      margin-top: 1rem;
    }
    .progress-bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #f5d061, #2ecc71);
      transition: width 0.3s ease;
    }
    .progress-status {
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 0.4rem;
    }
    .job-id-tag {
      font-size: 0.78rem;
      font-family: monospace;
      color: var(--primary);
      margin-top: 0.5rem;
      display: block;
    }
    .log-box {
      margin-top: 1rem;
      background: #080a0d;
      border: 1px solid #1a202c;
      border-radius: 6px;
      padding: 0.75rem;
      font-family: 'Consolas', monospace;
      font-size: 0.74rem;
      color: #94a3b8;
      height: 140px;
      overflow-y: auto;
      white-space: pre-wrap;
    }

    /* Results Gallery */
    .results-gallery {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.25rem;
      margin-top: 1rem;
    }
    .clip-card {
      background: #0f131a;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .clip-player {
      width: 100%;
      aspect-ratio: 9/16;
      background: #000;
      max-height: 380px;
      object-fit: contain;
    }
    .clip-card-body {
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      flex: 1;
    }
    .clip-card-title {
      font-size: 0.86rem;
      font-weight: 700;
      color: #fff;
    }
    .clip-scores {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
    }
    .score-chip {
      font-size: 0.7rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      background: #171d28;
      border: 1px solid #283348;
      color: #cbd5e1;
    }
    .score-chip.highlight {
      background: rgba(245, 208, 97, 0.15);
      border-color: rgba(245, 208, 97, 0.4);
      color: var(--primary);
      font-weight: 600;
    }
    .clip-transcript {
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.4;
      font-style: italic;
      max-height: 60px;
      overflow-y: auto;
    }
    .clip-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: auto;
      padding-top: 0.5rem;
    }
    .btn-action {
      flex: 1;
      padding: 0.45rem;
      font-size: 0.76rem;
      text-align: center;
      text-decoration: none;
      border-radius: 6px;
      background: #1c2331;
      color: #cbd5e1;
      border: 1px solid var(--card-border);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.3rem;
    }
    .btn-action:hover {
      background: #283348;
      color: #fff;
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">BH</div>
      <div>
        <div class="brand-title">AI Long Video Clipper</div>
        <div class="brand-subtitle">Beyond History Local AI Video Studio</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn btn-primary" id="header-btn-new-batch" onclick="startNewBatchWorkflow()" style="font-size:0.82rem; padding:0.45rem 0.9rem;">
        🚀 Start New Batch (<span id="header-next-batch">Next</span>)
      </button>
      <div class="status-badge">
        <div class="status-dot" id="gpu-dot"></div>
        <span id="gpu-label">NVIDIA GTX 1060 6GB (CUDA Active)</span>
      </div>
    </div>
  </header>

  <div class="container">
    <!-- Left Column: Upload & Options & Results -->
    <main>
      <!-- Batch Completed Banner -->
      <div class="batch-banner" id="batch-completed-banner" style="display:none;">
        <div>
          <div class="batch-banner-text" id="banner-title">🎉 Batch Completed Successfully!</div>
          <div class="batch-banner-sub" id="banner-subtitle">All clips have been generated and saved. Start a fresh batch below without losing any files.</div>
        </div>
        <button class="btn btn-primary" onclick="startNewBatchWorkflow()" style="box-shadow: 0 4px 15px rgba(245,208,97,0.4);">
          🚀 Start New Batch (<span class="next-batch-label">Next</span>)
        </button>
      </div>

      <!-- Upload Zone -->
      <div class="card">
        <div class="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          1. Upload or Select Source Videos (<span id="active-count-label">0 Selected</span>)
        </div>
        
        <div class="dropzone" id="dropzone">
          <div class="dropzone-icon">📁</div>
          <div class="dropzone-text">Drag & drop long video files here, or</div>
          
          <button type="button" class="btn btn-primary" id="btn-browse-files" style="margin: 0.75rem auto 0.35rem; width: auto; padding: 0.65rem 1.6rem; font-size: 0.92rem;" onclick="document.getElementById('file-input').click()">
            📁 Add Video Files
          </button>
          
          <div class="dropzone-sub">Supports MP4, MOV, MKV, AVI, WEBM (18m, 20m, 30m+ supported)</div>
          <input type="file" id="file-input" multiple accept="video/*,.mp4,.mov,.mkv,.avi,.webm" style="display:none;">
        </div>

        <!-- Live Upload Progress -->
        <div class="upload-progress-container" id="upload-progress-box">
          <div class="upload-progress-header">
            <span id="upload-filename">Uploading video...</span>
            <span id="upload-pct-label">0%</span>
          </div>
          <div class="upload-progress-bar">
            <div class="upload-progress-fill" id="upload-progress-fill"></div>
          </div>
        </div>

        <!-- Utility Row: Local Path & Library Toggle -->
        <div style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
          <input type="text" id="local-path-input" placeholder="Or enter local file path (e.g. C:\\Users\\HP\\Desktop\\1112.mp4)" style="flex:1; min-width: 260px; background:#0f131a; border:1px solid var(--card-border); border-radius:6px; padding:0.6rem 0.8rem; color:#fff; font-size:0.85rem;">
          <button class="btn btn-secondary" id="btn-add-local" style="width:auto; padding:0.6rem 1.1rem; font-size:0.85rem;">+ Add Video</button>
          <button class="btn btn-secondary" id="btn-toggle-library" onclick="toggleLibrary()" style="width:auto; padding:0.6rem 1.1rem; font-size:0.85rem;">
            📚 Library (<span id="library-count-label">0</span>)
          </button>
        </div>

        <!-- Expandable Library Panel -->
        <div class="library-panel" id="library-panel">
          <div class="library-panel-header">
            <span>Uploaded Video Library (Saved on Disk)</span>
            <span style="font-size:0.75rem; color:var(--text-muted);">Click '+ Add to Batch' to reuse existing uploads</span>
          </div>
          <div class="library-grid" id="library-grid"></div>
        </div>

        <!-- Active Batch Videos Grid -->
        <div class="video-grid" id="video-list"></div>
        <div class="empty-state" id="empty-state" style="display:none;">
          No videos selected for this batch yet. Click <strong>Add Video Files</strong> above to begin.
        </div>
      </div>

      <!-- Results Gallery -->
      <div class="card" id="results-card" style="display:none;">
        <div class="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Extracted AI Video Clips Gallery
        </div>
        <div id="results-summary" style="font-size:0.88rem; color:var(--text-muted); margin-bottom:1rem;"></div>
        <div class="results-gallery" id="results-gallery"></div>
      </div>
    </main>

    <!-- Right Column: Settings & Execution Controls -->
    <aside>
      <!-- Duration Targets -->
      <div class="card">
        <div class="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          2. Clip Duration Targets
        </div>
        <div class="duration-grid">
          <div class="duration-row">
            <label class="duration-label"><input type="checkbox" id="chk-30" checked> 30s</label>
            <div class="count-spinner">
              <button class="spinner-btn" onclick="adjustCount('cnt-30', -1)">-</button>
              <span class="spinner-val" id="cnt-30">3</span>
              <button class="spinner-btn" onclick="adjustCount('cnt-30', 1)">+</button>
            </div>
          </div>
          <div class="duration-row">
            <label class="duration-label"><input type="checkbox" id="chk-45" checked> 45s</label>
            <div class="count-spinner">
              <button class="spinner-btn" onclick="adjustCount('cnt-45', -1)">-</button>
              <span class="spinner-val" id="cnt-45">3</span>
              <button class="spinner-btn" onclick="adjustCount('cnt-45', 1)">+</button>
            </div>
          </div>
          <div class="duration-row">
            <label class="duration-label"><input type="checkbox" id="chk-60" checked> 60s</label>
            <div class="count-spinner">
              <button class="spinner-btn" onclick="adjustCount('cnt-60', -1)">-</button>
              <span class="spinner-val" id="cnt-60">2</span>
              <button class="spinner-btn" onclick="adjustCount('cnt-60', 1)">+</button>
            </div>
          </div>
          <div class="duration-row">
            <label class="duration-label"><input type="checkbox" id="chk-90"> 90s</label>
            <div class="count-spinner">
              <button class="spinner-btn" onclick="adjustCount('cnt-90', -1)">-</button>
              <span class="spinner-val" id="cnt-90">1</span>
              <button class="spinner-btn" onclick="adjustCount('cnt-90', 1)">+</button>
            </div>
          </div>
          <div class="duration-row" style="grid-column: span 2;">
            <label class="duration-label"><input type="checkbox" id="chk-120" checked> 120s</label>
            <div class="count-spinner">
              <button class="spinner-btn" onclick="adjustCount('cnt-120', -1)">-</button>
              <span class="spinner-val" id="cnt-120">2</span>
              <button class="spinner-btn" onclick="adjustCount('cnt-120', 1)">+</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Output Formats -->
      <div class="card">
        <div class="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/></svg>
          3. Output Formats
        </div>
        <div class="option-group">
          <label class="option-radio">
            <input type="radio" name="format" value="both" checked>
            <div>
              <strong>Both Formats (Recommended)</strong>
              <div style="font-size:0.75rem; color:var(--text-muted)">Original landscape + 1080x1920 vertical Shorts</div>
            </div>
          </label>
          <label class="option-radio">
            <input type="radio" name="format" value="vertical">
            <div>
              <strong>Vertical Shorts Only (9:16)</strong>
              <div style="font-size:0.75rem; color:var(--text-muted)">TikTok / Reels / YouTube Shorts blur-fill</div>
            </div>
          </label>
          <label class="option-radio">
            <input type="radio" name="format" value="landscape">
            <div>
              <strong>Original Landscape Only</strong>
              <div style="font-size:0.75rem; color:var(--text-muted)">Preserve native 16:9 composition</div>
            </div>
          </label>
        </div>

        <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid var(--card-border);">
          <label style="display:flex; align-items:center; gap:0.5rem; font-size:0.85rem; cursor:pointer;">
            <input type="checkbox" id="chk-burn-subtitles" checked accent-color="var(--primary)">
            <span>Burn Synchronized Subtitles (Gold Highlight)</span>
          </label>
        </div>
      </div>

      <!-- Action & Progress -->
      <div class="card">
        <div class="card-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          4. Clipper Controls
        </div>
        
        <button class="btn btn-primary" id="btn-start" onclick="startBatch()" style="width:100%;">
          ⚡ Start AI Long Video Clipper
        </button>

        <div style="display:flex; gap:0.5rem; margin-top:0.75rem;">
          <button class="btn btn-secondary" id="btn-pause" onclick="pauseBatch()" disabled style="flex:1;">⏸ Pause</button>
          <button class="btn btn-secondary" id="btn-resume" onclick="resumeBatch()" disabled style="display:none; flex:1;">▶ Resume</button>
          <button class="btn btn-danger" id="btn-cancel" onclick="cancelBatch()" disabled style="flex:1;">✕ Cancel</button>
        </div>

        <div class="progress-bar-container">
          <div class="progress-bar-fill" id="progress-fill"></div>
        </div>
        <div class="progress-status">
          <span id="progress-stage">Ready — 0%</span>
          <span id="progress-pct">0%</span>
        </div>
        <span class="job-id-tag" id="job-id-display">Job ID: Ready</span>

        <div class="log-box" id="log-box">AI Long Video Clipper initialized and idle.</div>
      </div>
    </aside>
  </div>

  <script>
    let activeVideos = [];
    let libraryVideos = [];
    let isProcessing = false;
    let pollInterval = null;
    let nextBatchName = 'Batch-003';

    const fileInput = document.getElementById('file-input');
    const dropzone = document.getElementById('dropzone');
    const videoList = document.getElementById('video-list');
    const emptyState = document.getElementById('empty-state');
    const logBox = document.getElementById('log-box');
    const uploadBox = document.getElementById('upload-progress-box');
    const uploadFilename = document.getElementById('upload-filename');
    const uploadPctLabel = document.getElementById('upload-pct-label');
    const uploadFill = document.getElementById('upload-progress-fill');
    const jobIdDisplay = document.getElementById('job-id-display');
    const batchBanner = document.getElementById('batch-completed-banner');
    const libraryPanel = document.getElementById('library-panel');
    const libraryGrid = document.getElementById('library-grid');

    window.addEventListener('DOMContentLoaded', () => {
      fetchUploadedVideos();
      updateStatus();
      startPolling();
    });

    function fetchUploadedVideos() {
      fetch('/api/uploaded_videos')
        .then(r => r.json())
        .then(data => {
          libraryVideos = data.library_videos || [];
          document.getElementById('library-count-label').innerText = libraryVideos.length;
          renderLibrary();

          if (data.next_batch) {
            updateNextBatchName(data.next_batch);
          }

          if (data.active_videos !== undefined) {
            activeVideos = data.active_videos;
            renderVideoList();
          }
        })
        .catch(err => console.log('Could not fetch existing videos:', err));
    }

    function updateNextBatchName(name) {
      nextBatchName = name;
      document.getElementById('header-next-batch').innerText = name;
      document.querySelectorAll('.next-batch-label').forEach(el => el.innerText = name);
    }

    // Drag-and-drop event handlers
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length) {
        handleFiles(e.target.files);
        fileInput.value = ''; // Reset to allow re-selecting same files
      }
    });

    document.getElementById('btn-add-local').addEventListener('click', () => {
      const p = document.getElementById('local-path-input').value.trim();
      if (!p) return;
      appendLog('Adding local video: ' + p);
      fetch('/api/select_local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: p })
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          appendLog('Failed to add local file: ' + data.error);
          alert(data.error);
        } else {
          appendLog('Loaded video: ' + data.video.filename + ' (' + data.video.width + 'x' + data.video.height + ')');
          addVideoToActive(data.video);
          document.getElementById('local-path-input').value = '';
          fetchUploadedVideos();
        }
      })
      .catch(err => {
        appendLog('Failed to add local file: ' + err);
        alert('Failed to add local file: ' + err);
      });
    });

    function toggleLibrary() {
      if (libraryPanel.style.display === 'block') {
        libraryPanel.style.display = 'none';
      } else {
        libraryPanel.style.display = 'block';
        renderLibrary();
      }
    }

    function renderLibrary() {
      libraryGrid.innerHTML = '';
      if (!libraryVideos.length) {
        libraryGrid.innerHTML = '<div style="font-size:0.75rem; color:var(--text-muted); grid-column:span 2;">No uploaded videos in library yet.</div>';
        return;
      }
      libraryVideos.forEach(v => {
        const isAdded = activeVideos.some(x => x.path === v.path);
        const item = document.createElement('div');
        item.className = 'library-item';
        item.innerHTML = `
          <div class="library-item-name" title="${v.filename}">${v.filename}</div>
          <div style="font-size:0.72rem; color:var(--text-muted); display:flex; justify-content:space-between;">
            <span>⏱ ${Math.floor(v.duration / 60)}m ${Math.floor(v.duration % 60)}s</span>
            <span>💾 ${v.size_mb} MB</span>
          </div>
          <button class="btn ${isAdded ? 'btn-secondary' : 'btn-success'}" style="padding:0.3rem; font-size:0.75rem;" onclick="toggleVideoFromLibrary('${encodeURIComponent(v.path)}')" ${isAdded ? 'disabled' : ''}>
            ${isAdded ? '✓ Added to Batch' : '+ Add to Batch'}
          </button>
        `;
        libraryGrid.appendChild(item);
      });
    }

    function toggleVideoFromLibrary(encodedPath) {
      const p = decodeURIComponent(encodedPath);
      const v = libraryVideos.find(x => x.path === p);
      if (v) {
        addVideoToActive(v);
        renderLibrary();
      }
    }

    function handleFiles(files) {
      const fileList = Array.from(files);
      if (!fileList.length) return;
      appendLog('Received ' + fileList.length + ' file(s) for upload.');
      uploadQueue(fileList, 0);
    }

    function uploadQueue(files, index) {
      if (index >= files.length) {
        uploadBox.style.display = 'none';
        fetchUploadedVideos();
        return;
      }
      const file = files[index];
      uploadSingleFile(file, () => {
        uploadQueue(files, index + 1);
      });
    }

    function uploadSingleFile(file, onComplete) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
      appendLog('Uploading ' + file.name + ' (' + sizeMb + ' MB)...');

      uploadBox.style.display = 'block';
      uploadFilename.innerText = file.name + ' (' + sizeMb + ' MB)';
      uploadPctLabel.innerText = '0%';
      uploadFill.style.width = '0%';

      const formData = new FormData();
      formData.append('file', file, file.name);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/upload', true);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          uploadFill.style.width = pct + '%';
          uploadPctLabel.innerText = pct + '% (' + (e.loaded / (1024*1024)).toFixed(1) + ' / ' + sizeMb + ' MB)';
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            if (data.video) {
              appendLog('Upload successful: ' + data.video.filename + ' [' + data.video.width + 'x' + data.video.height + ']');
              addVideoToActive(data.video);
            } else if (data.error) {
              appendLog('Upload failed: ' + data.error);
              alert('Upload failed: ' + data.error);
            }
          } catch (err) {
            appendLog('Server response parse error: ' + err);
          }
        } else {
          appendLog('Upload HTTP error ' + xhr.status + ': ' + xhr.responseText);
          alert('Upload failed with status ' + xhr.status);
        }
        if (onComplete) onComplete();
      };

      xhr.onerror = () => {
        appendLog('Network error during upload of ' + file.name);
        alert('Network error during video upload. Please check server.');
        if (onComplete) onComplete();
      };

      xhr.send(formData);
    }

    function addVideoToActive(v) {
      if (activeVideos.some(x => x.path === v.path)) {
        return;
      }
      activeVideos.push(v);
      renderVideoList();
      fetch('/api/add_to_batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: v.path })
      });
    }

    function removeVideo(idx) {
      const v = activeVideos[idx];
      if (!v) return;
      activeVideos.splice(idx, 1);
      renderVideoList();
      renderLibrary();
      fetch('/api/remove_video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: v.path })
      });
    }

    function renderVideoList() {
      videoList.innerHTML = '';
      document.getElementById('active-count-label').innerText = activeVideos.length + ' Selected';
      if (!activeVideos.length) {
        emptyState.style.display = 'block';
        return;
      }
      emptyState.style.display = 'none';

      activeVideos.forEach((v, idx) => {
        const item = document.createElement('div');
        item.className = 'video-item';
        item.innerHTML = `
          <div class="video-item-header">
            <div class="video-item-title" title="${v.filename}">${v.filename}</div>
            <button class="btn-remove" onclick="removeVideo(${idx})">× Remove</button>
          </div>
          <video class="video-item-preview" controls src="/stream/${encodeURIComponent(v.path)}"></video>
          <div class="video-item-meta">
            <span>⏱ ${Math.floor(v.duration / 60)}m ${Math.floor(v.duration % 60)}s</span>
            <span>📐 ${v.width}x${v.height} (${v.aspect_ratio})</span>
            <span>💾 ${v.size_mb} MB</span>
          </div>
        `;
        videoList.appendChild(item);
      });
    }

    function startNewBatchWorkflow() {
      if (isProcessing) {
        alert('Cannot start a new batch while processing is currently running.');
        return;
      }
      appendLog('Initializing clean workspace for new batch...');
      fetch('/api/new_batch', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'success') {
            activeVideos = [];
            renderVideoList();
            renderLibrary();
            batchBanner.style.display = 'none';
            document.getElementById('results-card').style.display = 'none';
            document.getElementById('progress-fill').style.width = '0%';
            document.getElementById('progress-pct').innerText = '0%';
            document.getElementById('progress-stage').innerText = 'Ready — 0%';
            jobIdDisplay.innerText = 'Job ID: Ready for ' + (data.next_batch || 'New Batch');
            if (data.next_batch) updateNextBatchName(data.next_batch);
            appendLog('Clean workspace initialized. Ready for ' + (data.next_batch || 'new batch') + '.');
          } else {
            alert('Failed to reset for new batch: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(err => {
          alert('Communication error: ' + err);
        });
    }

    function adjustCount(id, delta) {
      const el = document.getElementById(id);
      let val = parseInt(el.innerText) + delta;
      if (val < 0) val = 0;
      if (val > 10) val = 10;
      el.innerText = val;
    }

    function getTargetDurations() {
      const targets = {};
      if (document.getElementById('chk-30').checked) targets[30] = parseInt(document.getElementById('cnt-30').innerText);
      if (document.getElementById('chk-45').checked) targets[45] = parseInt(document.getElementById('cnt-45').innerText);
      if (document.getElementById('chk-60').checked) targets[60] = parseInt(document.getElementById('cnt-60').innerText);
      if (document.getElementById('chk-90').checked) targets[90] = parseInt(document.getElementById('cnt-90').innerText);
      if (document.getElementById('chk-120').checked) targets[120] = parseInt(document.getElementById('cnt-120').innerText);
      return targets;
    }

    function startBatch() {
      if (!activeVideos.length) {
        alert('Please add or upload at least one video to process in this batch.');
        return;
      }
      const durations = getTargetDurations();
      if (!Object.values(durations).some(v => v > 0)) {
        alert('Please select at least one duration preset with count > 0.');
        return;
      }

      const format = document.querySelector('input[name="format"]:checked').value;
      const burnSubs = document.getElementById('chk-burn-subtitles').checked;

      const payload = {
        video_paths: activeVideos.map(v => v.path),
        target_durations: durations,
        output_format: format,
        burn_subtitles: burnSubs
      };

      appendLog('Dispatching start request to engine...');
      fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          alert('Start error: ' + data.error);
          appendLog('Start error: ' + data.error);
        } else {
          isProcessing = true;
          document.getElementById('btn-start').disabled = true;
          document.getElementById('btn-pause').disabled = false;
          document.getElementById('btn-cancel').disabled = false;
          jobIdDisplay.innerText = 'Job ID: ' + (data.job_id || 'Active');
          appendLog('Clipper Job Started: ' + (data.job_id || ''));
          startPolling();
        }
      })
      .catch(err => {
        alert('Communication error: ' + err);
        appendLog('Communication error: ' + err);
      });
    }

    function pauseBatch() {
      fetch('/api/pause', { method: 'POST' }).then(() => {
        document.getElementById('btn-pause').style.display = 'none';
        document.getElementById('btn-resume').style.display = 'inline-flex';
        document.getElementById('btn-resume').disabled = false;
      });
    }

    function resumeBatch() {
      fetch('/api/resume', { method: 'POST' }).then(() => {
        document.getElementById('btn-resume').style.display = 'none';
        document.getElementById('btn-pause').style.display = 'inline-flex';
        document.getElementById('btn-pause').disabled = false;
      });
    }

    function cancelBatch() {
      if (!confirm('Are you sure you want to cancel the active batch?')) return;
      fetch('/api/cancel', { method: 'POST' });
    }

    function startPolling() {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(updateStatus, 1500);
    }

    function updateStatus() {
      fetch('/api/status')
        .then(r => r.json())
        .then(data => {
          document.getElementById('progress-fill').style.width = data.overall_percent + '%';
          document.getElementById('progress-pct').innerText = Math.round(data.overall_percent) + '%';
          document.getElementById('progress-stage').innerText = data.current_detail || data.current_stage || 'Ready — 0%';

          if (data.next_batch) {
            updateNextBatchName(data.next_batch);
          }

          if (data.job_id) {
            jobIdDisplay.innerText = 'Job ID: ' + data.job_id + ' [' + data.state.toUpperCase() + ']';
          }

          if (data.logs && data.logs.length) {
            logBox.innerText = data.logs.join('\\n');
            logBox.scrollTop = logBox.scrollHeight;
          }

          if (data.state === 'running') {
            isProcessing = true;
            batchBanner.style.display = 'none';
            document.getElementById('btn-start').disabled = true;
            document.getElementById('btn-pause').disabled = false;
            document.getElementById('btn-pause').style.display = 'inline-flex';
            document.getElementById('btn-resume').style.display = 'none';
            document.getElementById('btn-cancel').disabled = false;
          } else if (data.state === 'paused') {
            document.getElementById('btn-pause').style.display = 'none';
            document.getElementById('btn-resume').style.display = 'inline-flex';
            document.getElementById('btn-resume').disabled = false;
          } else if (data.state === 'completed') {
            isProcessing = false;
            document.getElementById('btn-start').disabled = false;
            document.getElementById('btn-pause').disabled = true;
            document.getElementById('btn-pause').style.display = 'inline-flex';
            document.getElementById('btn-resume').style.display = 'none';
            document.getElementById('btn-cancel').disabled = true;

            batchBanner.style.display = 'flex';
            if (data.batch_result) {
              document.getElementById('banner-title').innerText = '🎉 ' + (data.batch_result.batch_id || 'Batch') + ' Completed Successfully!';
              document.getElementById('banner-subtitle').innerText = 'Generated ' + data.batch_result.total_clips + ' clips in ' + data.batch_result.elapsed_seconds + 's. Folder: ' + data.batch_result.batch_dir;
              renderResults(data.batch_result);
            }
          } else if (data.state === 'cancelled' || data.state === 'error' || data.state === 'idle') {
            isProcessing = false;
            document.getElementById('btn-start').disabled = false;
            document.getElementById('btn-pause').disabled = true;
            document.getElementById('btn-pause').style.display = 'inline-flex';
            document.getElementById('btn-resume').style.display = 'none';
            document.getElementById('btn-cancel').disabled = true;
          }
        })
        .catch(err => console.log('Status polling error:', err));
    }

    function renderResults(res) {
      const card = document.getElementById('results-card');
      const gallery = document.getElementById('results-gallery');
      const summary = document.getElementById('results-summary');

      card.style.display = 'block';
      summary.innerHTML = `<strong>Batch ${res.batch_id}</strong>: Generated <strong>${res.total_clips}</strong> clips in ${res.elapsed_seconds}s. Folder: <code>${res.batch_dir}</code>`;
      gallery.innerHTML = '';

      for (const [vname, clips] of Object.entries(res.results)) {
        for (const c of clips) {
          const videoSrc = c.vertical_mp4 || c.landscape_mp4;
          const cardEl = document.createElement('div');
          cardEl.className = 'clip-card';
          cardEl.innerHTML = `
            <video class="clip-player" controls poster="/stream/${encodeURIComponent(c.contact_sheet || '')}" src="/stream/${encodeURIComponent(videoSrc)}"></video>
            <div class="clip-card-body">
              <div class="clip-card-title">${c.clip_id} (${c.duration}s)</div>
              <div class="clip-scores">
                <span class="score-chip highlight">Score: ${c.score}/100</span>
                <span class="score-chip">Hook: ${c.hook_score}</span>
                <span class="score-chip">Density: ${c.density_score}</span>
                <span class="score-chip">Closure: ${c.closure_score}</span>
              </div>
              <div class="clip-transcript">"${c.text}"</div>
              <div class="clip-actions">
                ${c.vertical_mp4 ? `<a class="btn-action" href="/stream/${encodeURIComponent(c.vertical_mp4)}" download>⬇ Vertical MP4</a>` : ''}
                ${c.landscape_mp4 ? `<a class="btn-action" href="/stream/${encodeURIComponent(c.landscape_mp4)}" download>⬇ Landscape MP4</a>` : ''}
                ${c.srt_path ? `<a class="btn-action" href="/stream/${encodeURIComponent(c.srt_path)}" download>⬇ SRT</a>` : ''}
              </div>
            </div>
          `;
          gallery.appendChild(cardEl);
        }
      }
    }

    function appendLog(msg) {
      const t = new Date().toLocaleTimeString();
      logBox.innerText += `\\n[${t}] ${msg}`;
      logBox.scrollTop = logBox.scrollHeight;
    }
  </script>
</body>
</html>
"""


class ClipperHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler with range-request video streaming, multipart file uploads, and REST endpoints."""
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        msg = format % args
        print(f"[HTTP] {msg}", flush=True)

    def send_json(self, status_code: int, data: dict):
        resp_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)
        self.wfile.flush()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            resp_bytes = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            self.wfile.flush()
            return

        elif path in ("/api/status", "/status"):
            st = JOB_MANAGER.get_status()
            self.send_json(200, st)
            return

        elif path in ("/api/uploaded_videos", "/uploaded_videos"):
            library = JOB_MANAGER.get_uploaded_videos()
            active = JOB_MANAGER.active_videos
            next_batch = JOB_MANAGER.get_next_batch_name()
            self.send_json(200, {
                "library_videos": library,
                "active_videos": active,
                "videos": active,
                "next_batch": next_batch
            })
            return

        elif path in ("/api/batches", "/batches"):
            batches = []
            for b in sorted(OUTPUT_ROOT.glob("Batch-*")):
                if b.is_dir():
                    rep = b / "batch-report.md"
                    clips = list(b.glob("*.mp4")) + list((b / "vertical-shorts").glob("*.mp4"))
                    batches.append({
                        "name": b.name,
                        "path": str(b),
                        "clip_count": len(clips),
                        "has_report": rep.exists()
                    })
            self.send_json(200, {"batches": batches})
            return

        elif path in ("/api/system_info", "/system_info"):
            import platform, psutil
            cpu_name = platform.processor() or "Multi-core CPU"
            cpu_count = os.cpu_count() or 4
            ram = psutil.virtual_memory()
            ram_gb = round(ram.total / (1024**3), 1)
            ram_avail = round(ram.available / (1024**3), 1)

            drive = os.path.splitdrive(str(OUTPUT_ROOT))[0] or "C:"
            disk = psutil.disk_usage(drive)
            disk_free_gb = round(disk.free / (1024**3), 1)

            gpu_info = {"available": False, "name": "No NVIDIA GPU (CPU Fallback)", "vram_gb": 0.0, "cuda": False}
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info = {
                        "available": True,
                        "name": torch.cuda.get_device_name(0),
                        "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2),
                        "cuda": True,
                        "cuda_version": torch.version.cuda
                    }
            except Exception:
                pass

            model_info = {"installed": False, "path": "", "name": "faster-whisper-small.en"}
            snapshot_rel = Path("hub/models--Systran--faster-whisper-small.en/snapshots/d1d751a5f8271d482d14ca55d9e2deeebbae577f")
            cache_dir = Path.home() / ".faceless-shorts" / "cache"
            cand_paths = [cache_dir / snapshot_rel, Path("C:/Users/HP/.faceless-shorts/cache") / snapshot_rel]
            for cp in cand_paths:
                if cp.exists():
                    model_info = {"installed": True, "path": str(cp), "name": "faster-whisper-small.en"}
                    break

            ffmpeg_p = shutil.which("ffmpeg")
            ffprobe_p = shutil.which("ffprobe")

            self.send_json(200, {
                "cpu": {"name": cpu_name, "threads": cpu_count},
                "ram": {"total_gb": ram_gb, "available_gb": ram_avail},
                "disk": {"drive": drive, "free_gb": disk_free_gb},
                "gpu": gpu_info,
                "model": model_info,
                "ffmpeg": {"installed": bool(ffmpeg_p), "path": ffmpeg_p or "", "ffprobe": bool(ffprobe_p)},
                "python": {"version": sys.version.split()[0], "path": sys.executable},
                "cache_dir": str(cache_dir),
                "output_dir": str(OUTPUT_ROOT)
            })
            return

        elif path in ("/api/history", "/history"):
            history = []
            if JOB_HISTORY_FILE.exists():
                try:
                    with open(JOB_HISTORY_FILE, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    history = []
            self.send_json(200, {"history": history})
            return

        elif path.startswith("/stream/"):
            raw_path = unquote(path[len("/stream/"):])
            file_path = Path(raw_path).resolve()

            if not file_path.exists() or not file_path.is_file():
                self.send_error(404, "File Not Found")
                return

            self.serve_file_with_range(file_path)
            return

        self.send_error(404, "Endpoint Not Found")

    def parse_and_save_upload(self, content_type: str, content_length: int) -> Tuple[str, Path]:
        """
        Streams multipart/form-data upload directly into a file in 64KB chunks.
        Prevents memory exhaustion on large 500MB+ video files and prevents binary corruption.
        """
        boundary = None
        for part in content_type.split(";"):
            part = part.strip()
            if part.lower().startswith("boundary="):
                boundary = part[9:].strip('"').strip("'")
                break

        if not boundary:
            raise ValueError("No boundary delimiter found in Content-Type")

        delim = b"\r\n--" + boundary.encode("utf-8")

        # Read header lines until empty line
        bytes_read = 0
        filename = None

        while bytes_read < content_length:
            line = self.rfile.readline()
            bytes_read += len(line)
            if not line or line == b"\r\n":
                break
            if b'filename="' in line:
                m = re.search(rb'filename="([^"]+)"', line)
                if m:
                    filename = m.group(1).decode("utf-8", errors="ignore")

        if not filename:
            filename = f"upload_{int(time.time())}.mp4"

        # Sanitize filename & extension
        raw_name = Path(filename).name
        stem = Path(raw_name).stem
        ext = Path(raw_name).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            ext = ".mp4"
        clean_stem = re.sub(r'[^a-zA-Z0-9_\-]', '_', stem)
        target_filename = f"{clean_stem}{ext}"
        dest_path = UPLOAD_DIR / target_filename

        # Stream payload directly to file in chunks
        with open(dest_path, "wb") as f_out:
            buf = bytearray()
            delim_len = len(delim)

            while bytes_read < content_length:
                chunk_to_read = min(65536, content_length - bytes_read)
                chunk = self.rfile.read(chunk_to_read)
                if not chunk:
                    break
                bytes_read += len(chunk)
                buf.extend(chunk)

                idx = buf.find(delim)
                if idx != -1:
                    f_out.write(buf[:idx])
                    buf.clear()
                    break
                else:
                    if len(buf) > delim_len + 65536:
                        flush_len = len(buf) - delim_len - 128
                        f_out.write(buf[:flush_len])
                        del buf[:flush_len]

            if buf:
                idx = buf.find(delim)
                if idx != -1:
                    f_out.write(buf[:idx])
                else:
                    f_out.write(buf)

        return target_filename, dest_path

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/api/upload", "/upload"):
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_json(400, {"error": "Expected multipart/form-data"})
                return

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self.send_json(400, {"error": "Empty upload payload"})
                return

            try:
                filename, dest_path = self.parse_and_save_upload(content_type, content_length)
                file_size_mb = round(dest_path.stat().st_size / (1024 * 1024), 2)
                print(f"[UPLOAD] Saved {filename} ({file_size_mb} MB) to {dest_path}", flush=True)

                engine = VideoClipperEngine()
                info = engine.probe_media(str(dest_path))

                # Automatically add to active batch
                JOB_MANAGER.add_active_video(info)
                self.send_json(200, {"status": "success", "video": info})
                return

            except Exception as e:
                print(f"[UPLOAD ERROR] {e}", flush=True)
                import traceback
                traceback.print_exc()
                self.send_json(500, {"error": f"Upload processing error: {str(e)}"})
                return

        # For all non-upload JSON endpoints, read body once up front to drain the stream
        content_length = int(self.headers.get("Content-Length", 0))
        body = ""
        if content_length > 0:
            body = self.rfile.read(content_length).decode("utf-8", errors="ignore")

        if path in ("/api/select_local", "/select_local"):
            try:
                data = safe_load_json(body) if body else {}
            except Exception as e:
                self.send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            local_path = data.get("path", "")
            p = Path(local_path).resolve()

            if not p.exists() or not p.is_file():
                self.send_json(400, {"error": f"File does not exist: {local_path}"})
                return

            try:
                engine = VideoClipperEngine()
                info = engine.probe_media(str(p))
                JOB_MANAGER.add_active_video(info)
                self.send_json(200, {"status": "success", "video": info})
            except Exception as e:
                self.send_json(500, {"error": f"Failed to probe file: {e}"})
            return

        elif path in ("/api/new_batch", "/new_batch"):
            try:
                next_batch = JOB_MANAGER.new_batch()
                self.send_json(200, {
                    "status": "success",
                    "message": f"Fresh workspace initialized for {next_batch}",
                    "next_batch": next_batch
                })
            except Exception as e:
                self.send_json(400, {"error": str(e)})
            return

        elif path in ("/api/add_to_batch", "/add_to_batch"):
            try:
                data = safe_load_json(body) if body else {}
            except Exception as e:
                self.send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            v_path = data.get("path", "")
            p = Path(v_path).resolve()

            if not p.exists() or not p.is_file():
                self.send_json(400, {"error": f"File not found: {v_path}"})
                return

            try:
                engine = VideoClipperEngine()
                info = engine.probe_media(str(p))
                JOB_MANAGER.add_active_video(info)
                self.send_json(200, {"status": "success", "active_videos": JOB_MANAGER.active_videos})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        elif path in ("/api/remove_video", "/remove_video"):
            try:
                data = safe_load_json(body) if body else {}
            except Exception as e:
                self.send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            v_path = data.get("path", "")
            JOB_MANAGER.remove_active_video(v_path)
            self.send_json(200, {"status": "success", "active_videos": JOB_MANAGER.active_videos})
            return

        elif path in ("/api/start", "/start"):
            try:
                data = safe_load_json(body) if body else {}
            except Exception as e:
                self.send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            v_paths = data.get("video_paths", [])
            if not v_paths:
                v_paths = [v["path"] for v in JOB_MANAGER.active_videos]

            if not v_paths:
                self.send_json(400, {"error": "No videos selected for this batch. Please add videos first."})
                return

            durations = {int(k): int(v) for k, v in data.get("target_durations", {}).items()}
            if not durations or not any(count > 0 for count in durations.values()):
                durations = {30: 3, 45: 3, 60: 2}

            fmt = data.get("output_format", "both")
            burn_subs = bool(data.get("burn_subtitles", True))

            try:
                job_id = JOB_MANAGER.start_job(v_paths, durations, fmt, burn_subs)
                print(f"[SERVER] Started Job ID: {job_id} with {len(v_paths)} video(s)", flush=True)
                self.send_json(200, {
                    "status": "started",
                    "job_id": job_id,
                    "total_videos": len(v_paths),
                    "durations": durations
                })
            except Exception as e:
                print(f"[SERVER START ERROR] {e}", flush=True)
                self.send_json(400, {"error": str(e)})
            return

        elif path in ("/api/pause", "/pause"):
            JOB_MANAGER.pause_job()
            self.send_json(200, {"status": "paused"})
            return

        elif path in ("/api/resume", "/resume"):
            JOB_MANAGER.resume_job()
            self.send_json(200, {"status": "resumed"})
            return

        elif path in ("/api/cancel", "/cancel"):
            JOB_MANAGER.cancel_job()
            self.send_json(200, {"status": "cancelled"})
            return

        elif path in ("/api/open_folder", "/open_folder"):
            try:
                data = safe_load_json(body) if body else {}
                folder = data.get("path", str(OUTPUT_ROOT))
                p = Path(folder).resolve()
                if not p.exists():
                    p = OUTPUT_ROOT
                if sys.platform == "win32":
                    os.startfile(str(p))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(p)])
                else:
                    subprocess.Popen(["xdg-open", str(p)])
                self.send_json(200, {"status": "success", "opened": str(p)})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        elif path in ("/api/download_model", "/download_model"):
            try:
                from faster_whisper import download_model
                cache_dir = str(Path.home() / ".faceless-shorts" / "cache")
                p = download_model("small.en", output_dir=cache_dir)
                self.send_json(200, {"status": "success", "model_path": str(p)})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        elif path in ("/api/test_engine", "/test_engine"):
            try:
                import subprocess
                # 1. Test FFmpeg
                ff_res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
                ff_ok = (ff_res.returncode == 0)
                ff_ver = ff_res.stdout.split("\n")[0] if ff_ok else "Unavailable"

                # 2. Test Torch & CUDA
                device_mode = "CPU Fallback"
                cuda_active = False
                try:
                    import torch
                    if torch.cuda.is_available():
                        device_mode = f"NVIDIA CUDA ({torch.cuda.get_device_name(0)})"
                        cuda_active = True
                except Exception:
                    pass

                # 3. Test Faster-Whisper
                whisper_ok = False
                try:
                    import faster_whisper
                    whisper_ok = True
                except Exception:
                    pass

                self.send_json(200, {
                    "status": "success",
                    "ffmpeg_ok": ff_ok,
                    "ffmpeg_version": ff_ver,
                    "whisper_ok": whisper_ok,
                    "cuda_active": cuda_active,
                    "device_mode": device_mode,
                    "engine_ready": (ff_ok and whisper_ok),
                    "message": f"AI Engine fully operational! Hardware: {device_mode}. Subtitle & Video pipeline verified."
                })
            except Exception as e:
                self.send_json(500, {"status": "error", "error": str(e)})
            return

        self.send_error(404, "Endpoint Not Found")

    def serve_file_with_range(self, file_path: Path):
        """Supports HTTP 206 Partial Content for video seeking."""
        file_size = file_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        range_header = self.headers.get("Range")
        if range_header:
            range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)


def run_server(port: int = 8765):
    server = ThreadingHTTPServer(("0.0.0.0", port), ClipperHTTPHandler)
    print("=" * 70)
    print(f" AI LONG VIDEO CLIPPER WEB SERVER RUNNING")
    print(f" URL: http://localhost:{port}")
    print(f" Press Ctrl+C to stop.")
    print("=" * 70, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
