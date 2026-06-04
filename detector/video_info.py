"""
Video Audit Tool — Task 2.0

Scans all video files in data/videos/ and extracts actual properties
using OpenCV. Generates video_report.json and video_report.md.

Usage:
    python detector/video_info.py
"""

import cv2
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VIDEO_DIR = os.environ.get("VIDEO_DIR", os.path.join("data", "videos"))
OUTPUT_DIR = os.environ.get("METADATA_DIR", os.path.join("data", "metadata"))

# Supported video extensions
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("video_audit")

# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------


def get_codec_name(fourcc_int: int) -> str:
    """Decode the FourCC integer into a human-readable codec string."""
    codec = "".join([chr((fourcc_int >> (8 * i)) & 0xFF) for i in range(4)])
    return codec.strip() if codec.strip() else "unknown"


def scan_video(filepath: str) -> dict[str, Any] | None:
    """
    Open a single video file with OpenCV and extract its properties.

    Returns a dict with video metadata or None on failure.
    """
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        logger.error("Failed to open video: %s", filepath)
        return None

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = get_codec_name(fourcc_int)

        duration_seconds = round(frame_count / fps, 2) if fps > 0 else 0.0
        file_size_bytes = os.path.getsize(filepath)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        report = {
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "fps": round(fps, 2),
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "duration_seconds": duration_seconds,
            "file_size_mb": file_size_mb,
            "codec": codec,
        }

        logger.info(
            "Scanned %s — %dx%d @ %.2f fps, %d frames, %.2fs, %.2f MB, codec=%s",
            report["filename"],
            width,
            height,
            fps,
            frame_count,
            duration_seconds,
            file_size_mb,
            codec,
        )
        return report

    finally:
        cap.release()


def scan_all_videos(video_dir: str) -> list[dict[str, Any]]:
    """Scan every video file inside *video_dir* and return a list of reports."""
    video_dir_path = Path(video_dir)
    if not video_dir_path.is_dir():
        logger.error("Video directory does not exist: %s", video_dir)
        return []

    video_files = sorted(
        [
            str(f)
            for f in video_dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
        ]
    )

    if not video_files:
        logger.warning("No video files found in %s", video_dir)
        return []

    logger.info("Found %d video file(s) in %s", len(video_files), video_dir)

    reports: list[dict[str, Any]] = []
    for filepath in video_files:
        result = scan_video(filepath)
        if result is not None:
            reports.append(result)

    return reports


# ---------------------------------------------------------------------------
# Report Writers
# ---------------------------------------------------------------------------


def write_json_report(reports: list[dict[str, Any]], output_dir: str) -> str:
    """Write video_report.json and return its path."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "video_report.json")

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_videos": len(reports),
        "videos": reports,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logger.info("JSON report written to %s", output_path)
    return output_path


def write_markdown_report(reports: list[dict[str, Any]], output_dir: str) -> str:
    """Write video_report.md and return its path."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "video_report.md")

    lines: list[str] = [
        "# Video Audit Report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Total Videos: {len(reports)}",
        "",
        "---",
        "",
    ]

    if reports:
        # Summary table
        lines.append(
            "| # | Filename | Resolution | FPS | Frames | Duration (s) | Size (MB) | Codec |"
        )
        lines.append(
            "|---|----------|------------|-----|--------|--------------|-----------|-------|"
        )
        for i, r in enumerate(reports, 1):
            lines.append(
                f"| {i} | {r['filename']} | {r['width']}x{r['height']} | "
                f"{r['fps']} | {r['frame_count']} | {r['duration_seconds']} | "
                f"{r['file_size_mb']} | {r['codec']} |"
            )
        lines.append("")

        # Per-video detail blocks
        for r in reports:
            lines.extend(
                [
                    f"## {r['filename']}",
                    "",
                    f"- **Resolution:** {r['width']} x {r['height']}",
                    f"- **FPS:** {r['fps']}",
                    f"- **Frame Count:** {r['frame_count']}",
                    f"- **Duration:** {r['duration_seconds']} seconds",
                    f"- **File Size:** {r['file_size_mb']} MB",
                    f"- **Codec:** {r['codec']}",
                    "",
                    "---",
                    "",
                ]
            )
    else:
        lines.append("No video files found.\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Markdown report written to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the full video audit pipeline."""
    logger.info("=== Video Audit Start ===")
    logger.info("Scanning directory: %s", VIDEO_DIR)

    reports = scan_all_videos(VIDEO_DIR)

    if not reports:
        logger.warning("No videos were successfully scanned. Reports will be empty.")

    json_path = write_json_report(reports, OUTPUT_DIR)
    md_path = write_markdown_report(reports, OUTPUT_DIR)

    print(f"\n{'='*60}")
    print(f"  Video Audit Complete")
    print(f"  Videos scanned: {len(reports)}")
    print(f"  JSON report:    {json_path}")
    print(f"  Markdown report: {md_path}")
    print(f"{'='*60}\n")

    logger.info("=== Video Audit Complete ===")


if __name__ == "__main__":
    # Ensure the project root is importable
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    main()
