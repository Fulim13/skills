#!/usr/bin/env python3

"""Extract deduplicated, timestamped frames from a video for note-taking."""

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

import imagehash
from PIL import Image


def sanitize_title(title: str) -> str:
    """Make a title safe for use in filenames."""
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title or "video"


def format_timestamp(total_seconds: float, separator: str = "-") -> str:
    """Convert seconds into HH-MM-SS format."""
    rounded_seconds = round(total_seconds)

    hours, remainder = divmod(rounded_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return separator.join(
        f"{value:02d}" for value in (hours, minutes, seconds)
    )


def check_dependencies() -> None:
    """Verify that FFmpeg is installed."""
    if shutil.which("ffmpeg") is None:
        print(
            "Error: FFmpeg is not installed or is not in PATH.",
            file=sys.stderr,
        )
        print(
            "Install it with: sudo apt install ffmpeg",
            file=sys.stderr,
        )
        raise SystemExit(1)


def extract_frames(
    video: Path,
    temporary_dir: Path,
    interval: float,
    max_width: int,
) -> None:
    """Extract one frame every specified number of seconds."""
    temporary_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = temporary_dir / "frame_%08d.jpg"

    filters = [f"fps=1/{interval}"]

    if max_width > 0:
        # -2 keeps the aspect ratio and an even height for the encoder.
        filters.append(f"scale='min({max_width},iw)':-2")

    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i",
        str(video),
        "-vf",
        ",".join(filters),
        "-start_number",
        "0",
        "-q:v",
        "2",
        str(output_pattern),
    ]

    print(f"Extracting one frame every {interval:g} seconds...")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as error:
        print(
            f"Error: FFmpeg failed with exit code {error.returncode}.",
            file=sys.stderr,
        )
        raise SystemExit(error.returncode) from error


def remove_duplicates_and_rename(
    temporary_dir: Path,
    output_dir: Path,
    title: str,
    threshold: int,
    interval: float,
) -> tuple[list[tuple[str, str, int]], int]:
    """
    Remove consecutive near-duplicate frames and rename retained frames.

    A larger threshold removes more similar images. Returns the retained
    frames as (filename, timestamp, seconds) plus the duplicate count.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    previous_kept_hash = None
    duplicate_count = 0
    kept: list[tuple[str, str, int]] = []

    frames = sorted(temporary_dir.glob("frame_*.jpg"))

    if not frames:
        print("Error: FFmpeg did not produce any frames.", file=sys.stderr)
        raise SystemExit(1)

    for frame in frames:
        match = re.fullmatch(r"frame_(\d+)", frame.stem)

        if match is None:
            continue

        frame_number = int(match.group(1))
        timestamp_seconds = frame_number * interval

        try:
            with Image.open(frame) as image:
                current_hash = imagehash.phash(
                    image.convert("RGB"),
                    hash_size=16,
                )
        except OSError as error:
            print(
                f"Warning: Could not read {frame.name}: {error}",
                file=sys.stderr,
            )
            continue

        hash_difference = None

        if previous_kept_hash is not None:
            hash_difference = current_hash - previous_kept_hash

        if (
            hash_difference is not None
            and hash_difference <= threshold
        ):
            duplicate_count += 1
            continue

        timestamp = format_timestamp(timestamp_seconds)
        destination = output_dir / f"{title}_{timestamp}.jpg"

        # Avoid overwriting when rounded timestamps are identical.
        if destination.exists():
            destination = output_dir / (
                f"{title}_{timestamp}_{frame_number:08d}.jpg"
            )

        shutil.copy2(frame, destination)

        previous_kept_hash = current_hash

        kept.append(
            (
                destination.name,
                format_timestamp(timestamp_seconds, separator=":"),
                round(timestamp_seconds),
            )
        )

    return kept, duplicate_count


def write_manifest(
    output_dir: Path,
    kept: list[tuple[str, str, int]],
) -> Path:
    """Write a frame-to-timestamp index for aligning frames with subtitles."""
    manifest = output_dir / "frames.tsv"

    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["filename", "timestamp", "seconds"])
        writer.writerows(kept)

    return manifest


def clear_output_directory(output_dir: Path) -> None:
    """Remove an existing output directory."""
    if output_dir.exists():
        shutil.rmtree(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract frames from a video at a fixed interval, remove "
            "near-duplicate frames, and name them with timestamps."
        )
    )

    parser.add_argument(
        "video",
        help="Path to the input video",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Seconds between frames; default: 10",
    )

    parser.add_argument(
        "--threshold",
        type=int,
        default=5,
        help=(
            "Duplicate similarity threshold; default: 5. "
            "Lower values remove fewer frames."
        ),
    )

    parser.add_argument(
        "--title",
        help=(
            "Title used in filenames; defaults to the video filename"
        ),
    )

    parser.add_argument(
        "--output",
        default="frames",
        help="Output directory; default: frames",
    )

    parser.add_argument(
        "--max-width",
        type=int,
        default=1280,
        help=(
            "Downscale frames wider than this; default: 1280. "
            "Use 0 to keep the original resolution."
        ),
    )

    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clear the existing output directory",
    )

    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be greater than 0")

    if args.threshold < 0:
        parser.error("--threshold cannot be negative")

    if args.max_width < 0:
        parser.error("--max-width cannot be negative")

    check_dependencies()

    video = Path(args.video).expanduser().resolve()

    if not video.is_file():
        print(
            f"Error: Video does not exist: {video}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    title = sanitize_title(args.title or video.stem)
    output_dir = Path(args.output).expanduser().resolve()

    temporary_dir = output_dir.parent / (
        f".{output_dir.name}_temporary"
    )

    if not args.keep_existing:
        clear_output_directory(output_dir)

    if temporary_dir.exists():
        shutil.rmtree(temporary_dir)

    try:
        extract_frames(
            video=video,
            temporary_dir=temporary_dir,
            interval=args.interval,
            max_width=args.max_width,
        )

        print("Removing near-duplicate frames...")

        kept, removed = remove_duplicates_and_rename(
            temporary_dir=temporary_dir,
            output_dir=output_dir,
            title=title,
            threshold=args.threshold,
            interval=args.interval,
        )
    finally:
        shutil.rmtree(temporary_dir, ignore_errors=True)

    manifest = write_manifest(output_dir, kept)

    print()
    print("Completed")
    print(f"Kept frames:       {len(kept)}")
    print(f"Removed duplicates:{removed}")
    print(f"Output directory:  {output_dir}")
    print(f"Frame index:       {manifest}")


if __name__ == "__main__":
    main()
