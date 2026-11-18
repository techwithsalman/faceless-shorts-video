"""AI Long Video Clipper - Command Line Interface (CLI)
Batch process long videos into AI-selected short clips with subtitles, scoring, and multi-format rendering.
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.clipper_engine import VideoClipperEngine


def parse_duration_arg(duration_strings) -> dict:
    """Parses duration strings like ['30:3', '45:3', '60:2', '120:2'] or [30, 45]."""
    res = {}
    if not duration_strings:
        # Defaults if none provided: 3x30s, 3x45s, 2x60s
        return {30: 3, 45: 3, 60: 2}

    for item in duration_strings:
        item = str(item).strip()
        if ":" in item:
            sec_str, count_str = item.split(":", 1)
            try:
                sec = int(sec_str)
                count = int(count_str)
                if sec > 0 and count > 0:
                    res[sec] = count
            except ValueError:
                pass
        else:
            try:
                sec = int(item)
                if sec > 0:
                    res[sec] = 1
            except ValueError:
                pass
    return res if res else {30: 3, 45: 3, 60: 2}


def progress_printer(data: dict):
    stage = data.get("stage", "working")
    pct = data.get("percent", 0.0)
    detail = data.get("detail", "")
    print(f"[{pct:5.1f}%] [{stage.upper()}] {detail}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="AI Long Video Clipper - Automatic Speech-Driven Clip Extraction and Formatting"
    )
    parser.add_argument(
        "--input", "-i", nargs="+", required=True,
        help="One or more video paths to process (MP4, MOV, MKV, AVI, WEBM)"
    )
    parser.add_argument(
        "--durations", "-d", nargs="+", default=["30:3", "45:3", "60:2", "120:2"],
        help="Target duration presets with counts, e.g. 30:3 45:3 60:2 120:2"
    )
    parser.add_argument(
        "--format", "-f", choices=["landscape", "vertical", "both"], default="both",
        help="Output video format: landscape, vertical (9:16 Shorts), or both"
    )
    parser.add_argument(
        "--no-subtitles", action="store_true",
        help="Disable burning subtitles onto the output video (SRT files still generated)"
    )
    parser.add_argument(
        "--output", "-o", default=str(Path(__file__).parent.parent / "AI-Video-Clips"),
        help="Output root folder for batches (default: ./AI-Video-Clips)"
    )
    parser.add_argument(
        "--device", choices=["cuda", "cpu", "auto"], default="auto",
        help="Device to use for Faster-Whisper (default: auto -> cuda if available)"
    )

    args = parser.parse_args()

    # Validate inputs
    valid_inputs = []
    for inp in args.input:
        p = Path(inp).resolve()
        if p.exists() and p.is_file():
            valid_inputs.append(str(p))
        else:
            print(f"[WARNING] Input video not found: {inp}")

    if not valid_inputs:
        print("[ERROR] No valid input videos specified. Exiting.")
        sys.exit(1)

    target_durations = parse_duration_arg(args.durations)

    print("=" * 70)
    print(" BEYOND HISTORY — AI LONG VIDEO CLIPPER")
    print("=" * 70)
    print(f"Input Videos:      {len(valid_inputs)}")
    for v in valid_inputs:
        print(f"  - {Path(v).name}")
    print(f"Target Durations:  {', '.join(f'{k}s ({v} clips)' for k, v in target_durations.items())}")
    print(f"Output Format:     {args.format.upper()}")
    print(f"Burn Subtitles:    {not args.no_subtitles}")
    print(f"Output Directory:  {args.output}")
    print(f"Device Mode:       {args.device}")
    print("=" * 70)

    engine = VideoClipperEngine(
        device=args.device,
        progress_callback=progress_printer
    )

    try:
        batch_result = engine.run_batch(
            video_paths=valid_inputs,
            output_root=args.output,
            target_durations=target_durations,
            output_format=args.format,
            burn_subtitles=not args.no_subtitles
        )

        print("\n" + "=" * 70)
        print(f"[SUCCESS] {batch_result['batch_id']} Completed!")
        print(f"Total Clips Generated: {batch_result['total_clips']}")
        print(f"Total Processing Time: {batch_result['elapsed_seconds']}s")
        print(f"Batch Folder:          {batch_result['batch_dir']}")
        print(f"Batch Report:          {batch_result['report_path']}")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n[CANCELLED] Operation aborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
