"""Cut one clip from the command line.

Example:
    python -m gameclip recording.mp4 01:12 01:27 -o output
"""

from __future__ import annotations

import argparse
import sys

from gameclip.clipping import extract_clip
from gameclip.errors import GameClipError


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, extract one clip, and print the output path."""
    parser = argparse.ArgumentParser(
        prog="gameclip",
        description="Cut a clip from an MP4 with FFmpeg.",
    )
    parser.add_argument("video", help="Path to the source MP4.")
    parser.add_argument("start", help="Start time in seconds or HH:MM:SS.")
    parser.add_argument("end", help="End time in seconds or HH:MM:SS.")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Directory for the clip. Created if missing. Default: output",
    )
    parser.add_argument(
        "-n",
        "--filename",
        default=None,
        help="Output file name, ending in .mp4. Default: <stem>_<start>-<end>.mp4",
    )
    args = parser.parse_args(argv)

    try:
        clip = extract_clip(
            args.video,
            args.start,
            args.end,
            output_dir=args.output_dir,
            filename=args.filename,
        )
    except GameClipError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(clip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
