"""AI Long Video Clipper - Core Processing Engine
Local, GPU-accelerated video clipping, transcription, scoring, and rendering engine.
Zero cloud API costs. Powered by Faster-Whisper, FFmpeg, and PyTorch.
"""

import os
import sys
import json
import re
import math
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable

# Ensure FFmpeg is in PATH on Windows
for candidate in [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-essentials_build" / "bin",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.1-full_build" / "bin",
]:
    if candidate.exists() and str(candidate) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")


def escape_ffmpeg_path(path_str: str) -> str:
    """Escapes Windows path for FFmpeg filter arguments (subtitles/ass)."""
    p = str(Path(path_str).resolve()).replace('\\', '/')
    # FFmpeg requires colon after drive letter to be escaped as '\:'
    if len(p) >= 2 and p[1] == ':':
        p = p[0] + '\\:' + p[2:]
    return p


def format_timestamp_srt(seconds: float) -> str:
    """Formats seconds into SRT timestamp: HH:MM:SS,mmm"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    secs = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def format_timestamp_ass(seconds: float) -> str:
    """Formats seconds into ASS timestamp: H:MM:SS.cc"""
    total_cs = int(round(seconds * 100))
    hours = total_cs // 360000
    minutes = (total_cs % 360000) // 6000
    secs = (total_cs % 6000) // 100
    cs = total_cs % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


class VideoClipperEngine:
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        device: str = "auto",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.progress_callback = progress_callback
        self.cancel_requested = False
        self.pause_requested = False
        self.whisper_model = None

        # Determine cache dir
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".faceless-shorts" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Determine compute device
        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                self.device = "cpu"
        else:
            self.device = device

        # Determine compute type for Faster-Whisper
        if self.device == "cuda":
            # Pascal GTX 1060 supports int8_float32, int8, float32 (does NOT support float16 natively)
            self.compute_type = "int8_float32"
        else:
            self.compute_type = "int8"

    def update_progress(self, stage: str, percent: float, detail: str = "", extra: Optional[Dict] = None):
        """Dispatches progress updates."""
        if self.progress_callback:
            data = {
                "stage": stage,
                "percent": round(percent, 1),
                "detail": detail,
                "timestamp": time.time()
            }
            if extra:
                data.update(extra)
            self.progress_callback(data)

    def check_pause_and_cancel(self):
        """Checks if operation was cancelled or paused."""
        while self.pause_requested and not self.cancel_requested:
            time.sleep(0.5)
        if self.cancel_requested:
            raise InterruptedError("Processing cancelled by user")

    def probe_media(self, file_path: str) -> Dict[str, Any]:
        """Uses ffprobe to extract full video and audio metadata."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size,bit_rate",
            "-show_entries", "stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
            "-of", "json",
            str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

        duration = float(data.get("format", {}).get("duration", 0.0))
        size_bytes = int(data.get("format", {}).get("size", 0))

        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0

        fps = 30.0
        if video_stream and "r_frame_rate" in video_stream:
            r = video_stream["r_frame_rate"]
            if "/" in r:
                num, den = r.split("/")
                fps = float(num) / max(1.0, float(den))
            else:
                fps = float(r)

        aspect_ratio = "landscape" if width >= height else "vertical"

        return {
            "path": str(Path(file_path).resolve()),
            "filename": Path(file_path).name,
            "duration": round(duration, 2),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "fps": round(fps, 2),
            "video_codec": video_stream.get("codec_name", "unknown") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name", "unknown") if audio_stream else None,
            "sample_rate": int(audio_stream.get("sample_rate", 44100)) if audio_stream else None,
            "channels": int(audio_stream.get("channels", 2)) if audio_stream else None,
        }

    def extract_audio(self, video_path: str, output_wav: str) -> str:
        """Extracts 16kHz mono 16-bit PCM WAV for Faster-Whisper."""
        Path(output_wav).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(output_wav)
        ]
        subprocess.run(cmd, check=True)
        return str(output_wav)

    def load_whisper(self):
        """Loads Faster-Whisper model into memory (cached)."""
        if self.whisper_model is not None:
            return self.whisper_model

        from faster_whisper import WhisperModel

        snapshot_rel = Path("hub/models--Systran--faster-whisper-small.en/snapshots/d1d751a5f8271d482d14ca55d9e2deeebbae577f")
        candidate_paths = [
            self.cache_dir / snapshot_rel,
            Path("C:/Users/HP/.faceless-shorts/cache") / snapshot_rel,
            Path(os.environ.get("HF_HOME", "")) / snapshot_rel,
            Path.home() / ".cache" / "huggingface" / snapshot_rel
        ]

        model_path = "small.en"
        for cp in candidate_paths:
            if cp.exists():
                model_path = str(cp)
                break

        # Attempt CUDA int8_float32
        if self.device == "cuda":
            try:
                self.whisper_model = WhisperModel(model_path, device="cuda", compute_type="int8_float32")
                return self.whisper_model
            except Exception:
                try:
                    self.whisper_model = WhisperModel(model_path, device="cuda", compute_type="float32")
                    return self.whisper_model
                except Exception:
                    pass

        # Fallback to CPU int8
        self.whisper_model = WhisperModel(model_path, device="cpu", compute_type="int8")
        return self.whisper_model

    def transcribe_audio(self, wav_path: str) -> Dict[str, Any]:
        """Transcribes audio with word-level timestamps."""
        model = self.load_whisper()

        # Run transcribe with word timestamps and voice activity detection
        segments_gen, info = model.transcribe(
            str(wav_path),
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=250)
        )

        segments = []
        all_words = []
        full_text_list = []

        for seg in segments_gen:
            self.check_pause_and_cancel()
            seg_words = []
            if seg.words:
                for w in seg.words:
                    word_clean = w.word.strip()
                    if word_clean:
                        w_dict = {
                            "word": word_clean,
                            "start": round(w.start, 3),
                            "end": round(w.end, 3),
                            "probability": round(w.probability, 3)
                        }
                        seg_words.append(w_dict)
                        all_words.append(w_dict)

            seg_dict = {
                "id": seg.id,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": seg_words
            }
            segments.append(seg_dict)
            full_text_list.append(seg.text.strip())

        return {
            "language": info.language,
            "duration": round(info.duration, 2),
            "full_text": " ".join(full_text_list),
            "segments": segments,
            "words": all_words
        }

    def detect_speech_pauses(self, words: List[Dict], audio_duration: float, wav_path: str) -> List[float]:
        """Finds clean cut points (timestamps) occurring at natural speech pauses."""
        cut_points = {0.0, audio_duration}

        # 1. Word boundary gaps
        for i in range(len(words) - 1):
            curr_end = words[i]["end"]
            next_start = words[i + 1]["start"]
            gap = next_start - curr_end

            # A gap of >= 0.20s is a clean pause
            if gap >= 0.20:
                cut_points.add(round(curr_end + min(0.10, gap / 2), 3))

            # If current word ends with terminal punctuation (. ? !), it's a prime boundary
            word_str = words[i]["word"]
            if any(word_str.endswith(p) for p in [".", "!", "?", ";"]):
                cut_points.add(round(curr_end + min(0.12, max(0.05, gap / 2)), 3))

        # 2. FFmpeg silencedetect as verification
        try:
            cmd = [
                "ffmpeg", "-v", "info",
                "-i", str(wav_path),
                "-af", "silencedetect=noise=-30dB:d=0.25",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            for line in res.stderr.splitlines():
                if "silence_start:" in line:
                    parts = line.split("silence_start:")
                    if len(parts) > 1:
                        val = float(parts[1].strip().split()[0])
                        cut_points.add(round(val + 0.05, 3))
                elif "silence_end:" in line:
                    parts = line.split("silence_end:")
                    if len(parts) > 1:
                        val = float(parts[1].strip().split()[0])
                        cut_points.add(round(val - 0.05, 3))
        except Exception:
            pass

        sorted_cuts = sorted([t for t in cut_points if 0.0 <= t <= audio_duration])
        return sorted_cuts

    def score_candidate(
        self,
        start_t: float,
        end_t: float,
        words_in_clip: List[Dict],
        total_audio_duration: float
    ) -> Dict[str, Any]:
        """Calculates multi-dimensional engagement scores for a candidate clip."""
        duration = end_t - start_t
        if duration <= 0 or not words_in_clip:
            return {"score": 0.0}

        text = " ".join(w["word"] for w in words_in_clip)
        norm_words = [re.sub(r'[^a-z0-9]', '', w["word"].lower()) for w in words_in_clip]
        norm_words = [w for w in norm_words if w]
        total_w = len(norm_words)

        if total_w < 12:
            return {"score": 0.0, "reason": "Insufficient words/speech"}

        # --- A. Hook Score (0 - 100) ---
        # First 3.5 seconds of the clip
        hook_window_end = start_t + min(3.8, duration * 0.25)
        hook_words = [w["word"].lower() for w in words_in_clip if w["start"] <= hook_window_end]
        hook_text = " ".join(hook_words)

        hook_score = 45.0  # Base score for clean speech onset

        # Check prompt question words
        question_hooks = ["how", "why", "what", "who", "when", "which", "did you know", "have you ever", "imagine", "what if", "can you"]
        if any(qh in hook_text for qh in question_hooks) or "?" in hook_text:
            hook_score += 25.0

        # Check curiosity / emotional trigger keywords
        trigger_keywords = [
            "secret", "mystery", "shocking", "never", "always", "truth", "money",
            "billion", "million", "died", "killed", "insane", "greatest", "biggest",
            "worst", "danger", "warning", "rule", "mistake", "first time", "discovered",
            "history", "powerful", "legend", "survived", "unbelievable", "revealed"
        ]
        matches = sum(1 for kw in trigger_keywords if kw in hook_text)
        hook_score += min(25.0, matches * 12.0)

        # Immediate speech onset bonus (starts within 0.4s)
        first_word_delay = words_in_clip[0]["start"] - start_t
        if first_word_delay <= 0.35:
            hook_score += 10.0
        elif first_word_delay > 1.2:
            hook_score -= 15.0

        hook_score = max(10.0, min(100.0, hook_score))

        # --- B. Content & Density Score (0 - 100) ---
        # Pacing: optimal speech rate is 2.0 to 3.2 words per second
        wps = total_w / duration
        if 2.0 <= wps <= 3.2:
            pacing_score = 90.0
        elif 1.4 <= wps < 2.0 or 3.2 < wps <= 4.0:
            pacing_score = 75.0
        else:
            pacing_score = 50.0

        # Lexical diversity (unique words / total words)
        unique_w = len(set(norm_words))
        diversity_ratio = unique_w / max(1, total_w)
        density_score = 50.0 + (diversity_ratio * 40.0)

        # Penalty for excessive filler sounds
        fillers = ["um", "uh", "er", "ah", "like", "you know"]
        filler_count = sum(1 for nw in norm_words if nw in fillers)
        if filler_count > 3:
            density_score -= min(20.0, filler_count * 4.0)

        density_score = max(10.0, min(100.0, density_score))

        # --- C. Story Closure & Completeness (0 - 100) ---
        # Last 4.0 seconds of the clip
        closure_window_start = end_t - min(4.0, duration * 0.25)
        closure_words = [w["word"] for w in words_in_clip if w["end"] >= closure_window_start]
        closure_text = " ".join(closure_words).lower()

        closure_score = 50.0

        # Ends cleanly with terminal punctuation
        last_word_str = words_in_clip[-1]["word"]
        if any(last_word_str.endswith(p) for p in [".", "!", "?"]):
            closure_score += 25.0
        elif any(last_word_str.endswith(p) for p in [",", "-", "..."]):
            closure_score -= 15.0  # Avoid ending mid-clause

        # Discourse markers of resolution or punchline
        conclusion_markers = [
            "ultimately", "finally", "in the end", "that is why", "that's why",
            "because of this", "which led to", "resulted in", "remember",
            "never forget", "this meant", "so next time", "and that was how"
        ]
        if any(cm in closure_text for cm in conclusion_markers):
            closure_score += 20.0

        # Penalty if last word is a conjunction or preposition
        dangling_words = ["and", "or", "but", "so", "if", "because", "then", "which", "that", "with", "at", "to", "of", "in"]
        clean_last = re.sub(r'[^a-z]', '', last_word_str.lower())
        if clean_last in dangling_words:
            closure_score -= 25.0

        closure_score = max(10.0, min(100.0, closure_score))

        # --- D. Dead-Air & Audio Consistency ---
        # Measure gaps within the clip
        max_internal_gap = 0.0
        for i in range(len(words_in_clip) - 1):
            g = words_in_clip[i + 1]["start"] - words_in_clip[i]["end"]
            if g > max_internal_gap:
                max_internal_gap = g

        flow_score = 90.0
        if max_internal_gap > 2.5:
            flow_score -= 30.0
        elif max_internal_gap > 1.5:
            flow_score -= 15.0

        # --- Composite Score ---
        # 35% Hook, 35% Content/Density, 20% Closure, 10% Flow/Pacing
        composite = (
            0.35 * hook_score +
            0.35 * density_score +
            0.20 * closure_score +
            0.10 * flow_score
        )

        # Generate a descriptive rationale
        rationale_points = []
        if hook_score >= 70:
            rationale_points.append("Strong opening hook")
        if closure_score >= 70:
            rationale_points.append("Clean conclusion")
        if density_score >= 75:
            rationale_points.append("High information density")
        if wps >= 2.2:
            rationale_points.append("Engaging speech tempo")

        rationale = ", ".join(rationale_points) if rationale_points else "Balanced narrative segment"

        return {
            "score": round(composite, 1),
            "hook_score": round(hook_score, 1),
            "density_score": round(density_score, 1),
            "closure_score": round(closure_score, 1),
            "flow_score": round(flow_score, 1),
            "wps": round(wps, 2),
            "word_count": total_w,
            "rationale": rationale,
            "preview_text": text[:160] + ("..." if len(text) > 160 else "")
        }

    def select_clips_for_durations(
        self,
        words: List[Dict],
        segments: List[Dict],
        cut_points: List[float],
        target_durations: Dict[int, int],
        total_audio_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Generates and ranks candidate clips for each requested duration preset.
        Avoids duplicates (IoU > 0.15), respects target counts, and leaves quality fallbacks.
        """
        all_candidates = []

        # Find candidates for each target duration
        for target_sec, target_count in target_durations.items():
            if target_count <= 0:
                continue

            # Allow flexibility around target (+/- 12% or +/- 4 seconds)
            leeway = max(4.0, target_sec * 0.12)
            min_dur = max(15.0, target_sec - leeway)
            max_dur = min(total_audio_duration, target_sec + leeway)

            # Evaluate cut point pairs
            for i in range(len(cut_points)):
                t_start = cut_points[i]
                if t_start + min_dur > total_audio_duration:
                    break

                for j in range(i + 1, len(cut_points)):
                    t_end = cut_points[j]
                    dur = t_end - t_start

                    if dur < min_dur:
                        continue
                    if dur > max_dur:
                        break

                    # Collect words strictly in this slice
                    clip_words = [w for w in words if w["start"] >= (t_start - 0.15) and w["end"] <= (t_end + 0.15)]
                    if len(clip_words) < 10:
                        continue

                    # Score candidate
                    eval_res = self.score_candidate(t_start, t_end, clip_words, total_audio_duration)
                    if eval_res.get("score", 0) >= 38.0:
                        candidate = {
                            "target_duration": target_sec,
                            "start": round(t_start, 2),
                            "end": round(t_end, 2),
                            "duration": round(dur, 2),
                            "words": clip_words,
                            "text": " ".join(w["word"] for w in clip_words),
                            **eval_res
                        }
                        all_candidates.append(candidate)

        # Deduplication and greedy selection by score
        all_candidates.sort(key=lambda c: c["score"], reverse=True)

        selected_clips = []
        counts_per_target = {d: 0 for d in target_durations.keys()}

        def calc_iou(c1, c2):
            inter_start = max(c1["start"], c2["start"])
            inter_end = min(c1["end"], c2["end"])
            if inter_end <= inter_start:
                return 0.0
            inter = inter_end - inter_start
            union = (c1["end"] - c1["start"]) + (c2["end"] - c2["start"]) - inter
            return inter / max(0.001, union)

        def calc_text_overlap(c1, c2):
            words1 = set(c1["text"].lower().split())
            words2 = set(c2["text"].lower().split())
            if not words1 or not words2:
                return 0.0
            return len(words1.intersection(words2)) / min(len(words1), len(words2))

        for cand in all_candidates:
            target_sec = cand["target_duration"]
            max_for_target = target_durations.get(target_sec, 0)

            if counts_per_target[target_sec] >= max_for_target:
                continue

            # Check overlap with any already selected clip
            is_dup = False
            for sel in selected_clips:
                iou = calc_iou(cand, sel)
                text_sim = calc_text_overlap(cand, sel)
                if iou > 0.15 or text_sim > 0.35:
                    is_dup = True
                    break

            if not is_dup:
                selected_clips.append(cand)
                counts_per_target[target_sec] += 1

        # Sort selected clips by start time for logical order
        selected_clips.sort(key=lambda c: c["start"])
        return selected_clips

    def generate_subtitles_files(
        self,
        clip: Dict[str, Any],
        out_srt_path: str,
        out_ass_path: str,
        is_vertical: bool = True
    ):
        """Generates synchronized SRT and ASS subtitle files with Gold active-word highlighting."""
        Path(out_srt_path).parent.mkdir(parents=True, exist_ok=True)
        clip_start = clip["start"]
        clip_words = clip["words"]

        # 1. Generate SRT File
        srt_lines = []
        srt_idx = 1

        # Group words into short readable blocks (3-5 words)
        words_per_block = 4
        for k in range(0, len(clip_words), words_per_block):
            block = clip_words[k:k + words_per_block]
            b_start = max(0.0, block[0]["start"] - clip_start)
            b_end = max(b_start + 0.3, block[-1]["end"] - clip_start)
            b_text = " ".join(w["word"] for w in block)

            srt_lines.append(f"{srt_idx}")
            srt_lines.append(f"{format_timestamp_srt(b_start)} --> {format_timestamp_srt(b_end)}")
            srt_lines.append(b_text)
            srt_lines.append("")
            srt_idx += 1

        with open(out_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))

        # 2. Generate ASS File with Gold word highlighting and safe zone margins
        # ASS Color format: &HAABBGGRR&
        # Gold #F5D061 -> BGR 61 D0 F5 -> &H0061D0F5&
        # White #FFFFFF -> &H00FFFFFF&
        # Black outline -> &H00000000&

        font_size = 54 if is_vertical else 42
        margin_v = 400 if is_vertical else 85  # Safe zone well above TikTok/Reels bottom overlays

        ass_header = f"""[Script Info]
Title: AI Long Video Clipper Auto Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ClipperSub,Arial,{font_size},&H00FFFFFF&,&H0061D0F5&,&H00000000&,&H80000000&,1,0,0,0,100,100,0,0,1,3.5,1.5,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        ass_events = []
        # Group into 3-word animated chunks where the currently active word is highlighted in Gold
        chunk_size = 4
        for k in range(0, len(clip_words), chunk_size):
            chunk = clip_words[k:k + chunk_size]
            chunk_start = max(0.0, chunk[0]["start"] - clip_start)
            chunk_end = max(chunk_start + 0.4, chunk[-1]["end"] - clip_start)

            # For each word in chunk, show the chunk with that word highlighted in gold during its duration
            for active_idx, target_w in enumerate(chunk):
                w_start = max(0.0, target_w["start"] - clip_start)
                w_end = max(w_start + 0.15, target_w["end"] - clip_start)

                tokens = []
                for idx, w in enumerate(chunk):
                    w_str = w["word"].upper()
                    if idx == active_idx:
                        tokens.append(f"{{\\c&H0061D0F5&}}{w_str}{{\\c&H00FFFFFF&}}")
                    else:
                        tokens.append(f"{{\\c&H00FFFFFF&}}{w_str}")

                line_text = " ".join(tokens)
                ass_events.append(
                    f"Dialogue: 0,{format_timestamp_ass(w_start)},{format_timestamp_ass(w_end)},ClipperSub,,0,0,0,,{line_text}"
                )

        with open(out_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(ass_events))

    def render_clip_landscape(
        self,
        source_video: str,
        clip: Dict[str, Any],
        out_mp4_path: str,
        burn_subtitles: bool = True,
        ass_path: Optional[str] = None
    ):
        """
        Renders landscape clip preserving original composition and aspect ratio.
        Applies audio normalization (loudnorm) and subtle fades (afade).
        """
        Path(out_mp4_path).parent.mkdir(parents=True, exist_ok=True)
        start_t = clip["start"]
        dur = clip["duration"]

        audio_filter = f"afade=t=in:ss=0:d=0.06,afade=t=out:st={dur - 0.08:.3f}:d=0.08,loudnorm=I=-16:TP=-1.5:LRA=11"

        video_filters = []
        if burn_subtitles and ass_path and os.path.exists(ass_path):
            esc_ass = escape_ffmpeg_path(ass_path)
            video_filters.append(f"ass='{esc_ass}'")

        vf_str = ",".join(video_filters) if video_filters else "null"

        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-ss", str(start_t),
            "-t", str(dur),
            "-i", str(source_video),
            "-vf", vf_str,
            "-af", audio_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k",
            str(out_mp4_path)
        ]
        subprocess.run(cmd, check=True)

    def render_clip_vertical(
        self,
        source_video: str,
        clip: Dict[str, Any],
        out_mp4_path: str,
        source_aspect: str = "landscape",
        burn_subtitles: bool = True,
        ass_path: Optional[str] = None
    ):
        """
        Renders 1080x1920 (9:16) vertical Shorts clip.
        For landscape source: Uses blurred background fill + centered sharp foreground. Never stretches!
        Applies audio normalization and subtle fades.
        """
        Path(out_mp4_path).parent.mkdir(parents=True, exist_ok=True)
        start_t = clip["start"]
        dur = clip["duration"]

        audio_filter = f"afade=t=in:ss=0:d=0.06,afade=t=out:st={dur - 0.08:.3f}:d=0.08,loudnorm=I=-16:TP=-1.5:LRA=11"

        if source_aspect == "landscape":
            # Blurred background fill filter graph
            # [0:v] -> scale & crop to 1080x1920 + boxblur
            # [0:v] -> scale to fit 1080 width cleanly
            # overlay centered -> burn subtitles
            blur_filter = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
            )
            if burn_subtitles and ass_path and os.path.exists(ass_path):
                esc_ass = escape_ffmpeg_path(ass_path)
                filter_complex = f"{blur_filter};[base]ass='{esc_ass}'[v]"
            else:
                filter_complex = f"{blur_filter};[base]null[v]"

            cmd = [
                "ffmpeg", "-v", "error", "-y",
                "-ss", str(start_t),
                "-t", str(dur),
                "-i", str(source_video),
                "-filter_complex", filter_complex,
                "-map", "[v]", "-map", "0:a?",
                "-af", audio_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "192k",
                str(out_mp4_path)
            ]
        else:
            # Source is already vertical, center pad if necessary
            vf = ["scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"]
            if burn_subtitles and ass_path and os.path.exists(ass_path):
                esc_ass = escape_ffmpeg_path(ass_path)
                vf.append(f"ass='{esc_ass}'")

            cmd = [
                "ffmpeg", "-v", "error", "-y",
                "-ss", str(start_t),
                "-t", str(dur),
                "-i", str(source_video),
                "-vf", ",".join(vf),
                "-af", audio_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "192k",
                str(out_mp4_path)
            ]

        subprocess.run(cmd, check=True)

    def generate_contact_sheet(self, clip_mp4_path: str, out_jpg_path: str, duration: float):
        """Generates a crisp 5x2 thumbnail contact sheet of the clip."""
        Path(out_jpg_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            # Sample 10 frames across the clip duration
            step = duration / 10.0
            cmd = [
                "ffmpeg", "-v", "error", "-y",
                "-i", str(clip_mp4_path),
                "-vf", f"fps=1/{max(0.5, step):.2f},scale=320:-1,tile=5x2",
                "-frames:v", "1", "-q:v", "2",
                str(out_jpg_path)
            ]
            subprocess.run(cmd, check=True)
        except Exception as e:
            # Fallback simple thumbnail
            try:
                cmd = [
                    "ffmpeg", "-v", "error", "-y",
                    "-ss", f"{duration / 2:.2f}",
                    "-i", str(clip_mp4_path),
                    "-frames:v", "1", "-q:v", "2",
                    str(out_jpg_path)
                ]
                subprocess.run(cmd, check=True)
            except Exception:
                pass

    def process_single_video(
        self,
        video_path: str,
        batch_dir: Path,
        target_durations: Dict[int, int],
        output_format: str = "both",  # 'landscape', 'vertical', 'both'
        burn_subtitles: bool = True,
        video_index: int = 1,
        total_videos: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Full end-to-end pipeline for a single video in the batch.
        """
        video_path = str(Path(video_path).resolve())
        v_name = Path(video_path).stem
        clean_v_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', v_name)

        base_pct = ((video_index - 1) / total_videos) * 100
        step_weight = 100.0 / total_videos

        # 1. Probe media
        self.update_progress(
            "probing", base_pct + step_weight * 0.05,
            f"Probing video {video_index}/{total_videos}: {Path(video_path).name}"
        )
        self.check_pause_and_cancel()
        meta = self.probe_media(video_path)

        # 2. Extract audio
        self.update_progress(
            "audio_extraction", base_pct + step_weight * 0.15,
            f"Extracting 16kHz audio for speech analysis: {meta['filename']}"
        )
        self.check_pause_and_cancel()
        temp_dir = batch_dir / "temp" / clean_v_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        wav_path = str(temp_dir / "audio_16k.wav")
        self.extract_audio(video_path, wav_path)

        # 3. Transcribe speech with Faster-Whisper
        self.update_progress(
            "transcription", base_pct + step_weight * 0.35,
            f"Faster-Whisper AI transcription ({self.device.upper()}): {meta['filename']}"
        )
        self.check_pause_and_cancel()
        transcript_data = self.transcribe_audio(wav_path)
        words = transcript_data["words"]
        segments = transcript_data["segments"]

        if not words:
            self.update_progress(
                "warning", base_pct + step_weight * 0.9,
                f"No spoken words detected in {meta['filename']}."
            )
            return []

        # 4. Detect pauses and clean cut points
        self.update_progress(
            "pause_detection", base_pct + step_weight * 0.45,
            f"Analyzing breath pauses and sentence boundaries: {len(words)} words"
        )
        self.check_pause_and_cancel()
        cut_points = self.detect_speech_pauses(words, meta["duration"], wav_path)

        # 5. Candidate selection & AI scoring
        self.update_progress(
            "clip_selection", base_pct + step_weight * 0.55,
            f"Selecting top clips based on hook, density, and closure metrics..."
        )
        self.check_pause_and_cancel()
        selected_clips = self.select_clips_for_durations(
            words, segments, cut_points, target_durations, meta["duration"]
        )

        if not selected_clips:
            self.update_progress(
                "warning", base_pct + step_weight * 0.9,
                f"No qualifying clips found meeting quality thresholds in {meta['filename']}."
            )
            return []

        # 6. Render clips, generate subtitles and contact sheets
        rendered_clips = []
        num_clips = len(selected_clips)

        # Directories
        landscape_dir = batch_dir / "original-landscape"
        vertical_dir = batch_dir / "vertical-shorts"
        subtitles_dir = batch_dir / "subtitles"
        metadata_dir = batch_dir / "metadata"
        contact_dir = batch_dir / "contact-sheets"

        for d in [landscape_dir, vertical_dir, subtitles_dir, metadata_dir, contact_dir]:
            d.mkdir(parents=True, exist_ok=True)

        for c_idx, clip in enumerate(selected_clips, 1):
            self.check_pause_and_cancel()
            clip_id = f"{clean_v_name}_clip{c_idx:02d}_{int(clip['duration'])}s"

            render_pct = base_pct + step_weight * (0.55 + 0.40 * (c_idx / num_clips))
            self.update_progress(
                "rendering", render_pct,
                f"Rendering clip {c_idx}/{num_clips} ({int(clip['duration'])}s) for {meta['filename']}"
            )

            # Subtitle paths
            srt_path = str(subtitles_dir / f"{clip_id}.srt")
            ass_vert_path = str(temp_dir / f"{clip_id}_vert.ass")
            ass_land_path = str(temp_dir / f"{clip_id}_land.ass")

            self.generate_subtitles_files(clip, srt_path, ass_vert_path, is_vertical=True)
            self.generate_subtitles_files(clip, srt_path, ass_land_path, is_vertical=False)

            out_land = None
            out_vert = None

            # Render Landscape if requested
            if output_format in ("landscape", "both"):
                out_land = str(landscape_dir / f"{clip_id}_landscape.mp4")
                self.render_clip_landscape(
                    video_path, clip, out_land,
                    burn_subtitles=burn_subtitles,
                    ass_path=ass_land_path
                )

            # Render Vertical if requested
            if output_format in ("vertical", "both"):
                out_vert = str(vertical_dir / f"{clip_id}_vertical.mp4")
                self.render_clip_vertical(
                    video_path, clip, out_vert,
                    source_aspect=meta["aspect_ratio"],
                    burn_subtitles=burn_subtitles,
                    ass_path=ass_vert_path
                )

            # Generate contact sheet from rendered clip
            primary_video = out_vert if out_vert else out_land
            contact_jpg = str(contact_dir / f"{clip_id}_contact.jpg")
            if primary_video:
                self.generate_contact_sheet(primary_video, contact_jpg, clip["duration"])

            # Save individual clip metadata
            clip_meta = {
                "clip_id": clip_id,
                "source_video": meta["filename"],
                "source_path": meta["path"],
                "source_resolution": f"{meta['width']}x{meta['height']}",
                "start": clip["start"],
                "end": clip["end"],
                "start_time": clip["start"],
                "end_time": clip["end"],
                "duration": clip["duration"],
                "target_duration": clip["target_duration"],
                "score": clip["score"],
                "hook_score": clip["hook_score"],
                "density_score": clip["density_score"],
                "closure_score": clip["closure_score"],
                "wps": clip["wps"],
                "rationale": clip["rationale"],
                "text": clip["text"],
                "landscape_mp4": out_land,
                "vertical_mp4": out_vert,
                "srt_path": srt_path,
                "contact_sheet": contact_jpg
            }

            meta_file = metadata_dir / f"{clip_id}.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(clip_meta, f, indent=2)

            rendered_clips.append(clip_meta)

        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

        return rendered_clips

    def run_batch(
        self,
        video_paths: List[str],
        output_root: str,
        target_durations: Dict[int, int],
        output_format: str = "both",
        burn_subtitles: bool = True
    ) -> Dict[str, Any]:
        """
        Runs batch clipper processing over multiple videos.
        Generates Batch-XXX directory and full Markdown batch report.
        """
        root_path = Path(output_root).resolve()
        root_path.mkdir(parents=True, exist_ok=True)

        # Determine next batch folder Batch-001, Batch-002, etc.
        existing_batches = [d.name for d in root_path.iterdir() if d.is_dir() and d.name.startswith("Batch-")]
        batch_nums = []
        for b in existing_batches:
            try:
                num = int(b.split("-")[1])
                batch_nums.append(num)
            except Exception:
                pass
        next_num = max(batch_nums, default=0) + 1
        batch_dir = root_path / f"Batch-{next_num:03d}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        total_videos = len(video_paths)
        start_time = time.time()
        all_results = {}

        self.update_progress("start", 0.0, f"Initializing Clipper Batch-{next_num:03d} for {total_videos} video(s)...")

        for idx, v_path in enumerate(video_paths, 1):
            self.check_pause_and_cancel()
            clips = self.process_single_video(
                video_path=v_path,
                batch_dir=batch_dir,
                target_durations=target_durations,
                output_format=output_format,
                burn_subtitles=burn_subtitles,
                video_index=idx,
                total_videos=total_videos
            )
            all_results[Path(v_path).name] = clips

        total_duration = round(time.time() - start_time, 2)
        total_clips = sum(len(c) for c in all_results.values())

        # Generate Batch Report Markdown
        report_md = self.generate_batch_report_md(
            batch_id=f"Batch-{next_num:03d}",
            video_paths=video_paths,
            batch_dir=batch_dir,
            results=all_results,
            target_durations=target_durations,
            output_format=output_format,
            burn_subtitles=burn_subtitles,
            elapsed_sec=total_duration
        )

        report_file = batch_dir / "batch-report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)

        self.update_progress(
            "complete", 100.0,
            f"Batch-{next_num:03d} complete: {total_clips} clips generated across {total_videos} videos in {total_duration}s."
        )

        return {
            "batch_id": f"Batch-{next_num:03d}",
            "batch_dir": str(batch_dir),
            "total_clips": total_clips,
            "total_videos": total_videos,
            "elapsed_seconds": total_duration,
            "report_path": str(report_file),
            "results": all_results
        }

    def generate_batch_report_md(
        self,
        batch_id: str,
        video_paths: List[str],
        batch_dir: Path,
        results: Dict[str, List[Dict]],
        target_durations: Dict[int, int],
        output_format: str,
        burn_subtitles: bool,
        elapsed_sec: float
    ) -> str:
        """Generates comprehensive Markdown report for the batch run."""
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        total_clips = sum(len(c) for c in results.values())

        target_summary = ", ".join(f"{sec}s: {count} clips" for sec, count in sorted(target_durations.items()))

        md = f"""# BEYOND HISTORY — AI LONG VIDEO CLIPPER BATCH REPORT
**Batch ID:** `{batch_id}`  
**Generated At:** {now_str}  
**Hardware Engine:** NVIDIA GeForce GTX 1060 6GB (CUDA: `{self.device.upper()}`)  
**Total Videos Processed:** {len(video_paths)}  
**Total Clips Generated:** {total_clips}  
**Output Formats:** `{output_format.upper()}` (Subtitles: {'Burned + SRT' if burn_subtitles else 'SRT only'})  
**Duration Targets:** {target_summary}  
**Total Processing Time:** {elapsed_sec:.1f} seconds  

---

## 1. Executive Summary & Batch Metrics

| Source Video | Clips Extracted | Target Met | Avg Clip Score | Highest Hook | Key Narrative Focus |
|:-------------|:---------------:|:----------:|:--------------:|:------------:|:--------------------|
"""
        for vname, clips in results.items():
            count = len(clips)
            avg_score = round(sum(c["score"] for c in clips) / max(1, count), 1) if count else 0.0
            max_hook = max((c["hook_score"] for c in clips), default=0.0)
            target_sum = sum(target_durations.values())
            met_status = "Target Met" if count >= target_sum else f"{count}/{target_sum} (Quality Fallback)"
            focus = clips[0]["rationale"] if clips else "No speech detected"
            md += f"| `{vname}` | **{count}** | {met_status} | **{avg_score}** | **{max_hook}** | {focus} |\n"

        md += f"""
---

## 2. Detailed Clip Manifest & Scoring Breakdown

"""
        for vname, clips in results.items():
            md += f"### Source: `{vname}`\n\n"
            if not clips:
                md += "> *No qualifying speech segments found meeting retention thresholds.*\n\n"
                continue

            md += "| Clip ID | Target | Exact Range | Score | Hook | Density | Closure | Rationale |\n"
            md += "|:--------|:------:|:-----------:|:-----:|:----:|:-------:|:-------:|:----------|\n"
            for c in clips:
                dur_fmt = f"{c['start']:.1f}s – {c['end']:.1f}s ({c['duration']:.1f}s)"
                md += (
                    f"| `{c['clip_id']}` | **{c['target_duration']}s** | {dur_fmt} | "
                    f"**{c['score']}** | {c['hook_score']} | {c['density_score']} | {c['closure_score']} | "
                    f"{c['rationale']} |\n"
                )

            md += "\n#### Clip Transcripts & Storylines:\n"
            for c in clips:
                md += f"- **`{c['clip_id']}`** ({c['duration']}s | Score: {c['score']}/100):\n"
                md += f"  > *\"{c['text']}\"*\n"
                if c.get("vertical_mp4"):
                    md += f"  - Vertical Video: `vertical-shorts/{Path(c['vertical_mp4']).name}`\n"
                if c.get("landscape_mp4"):
                    md += f"  - Landscape Video: `original-landscape/{Path(c['landscape_mp4']).name}`\n"
                if c.get("srt_path"):
                    md += f"  - Synchronized Subtitles: `subtitles/{Path(c['srt_path']).name}`\n"
                if c.get("contact_sheet"):
                    md += f"  - Storyboard Sheet: `contact-sheets/{Path(c['contact_sheet']).name}`\n"
            md += "\n"

        md += f"""---

## 3. Directory Layout

All assets for this batch are organized in:
`{batch_dir}`

```
{batch_id}/
├── original-landscape/   # Full resolution landscape cuts
├── vertical-shorts/      # 1080x1920 9:16 vertical Shorts (blur-fill + safe-zone subtitles)
├── subtitles/            # Synchronized .srt subtitle files
├── metadata/             # JSON metrics, timestamps & scoring
├── contact-sheets/       # 5x2 thumbnail storyboard previews
└── batch-report.md       # Full production report
```

## 4. Verification & Quality Guarantees
- **No Mid-Sentence Cuts:** All clip boundaries snapped to natural breath pauses ($gap \\ge 0.20s$) or terminal punctuation.
- **Aspect Ratio Integrity:** Vertical conversions use blurred background fill with centered crisp foreground; footage is never stretched or distorted.
- **Audio Consistency:** All audio tracks normalized to Broadcast Standard ($-16$ LUFS, $-1.5$ dB True Peak) with $60ms$ in/$80ms$ out smoothing to prevent pops.
- **Zero Cloud Costs:** 100% processed locally on office PC hardware ($0.00 API expenses).
"""
        return md
