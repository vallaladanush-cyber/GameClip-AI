"""Validate a local MP4 before any clipping work begins."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from gameclip.errors import VideoValidationError
from gameclip.media import require_binary, run_command


@dataclass(frozen=True)
class VideoFile:
    """An MP4 that exists, is readable, and contains a video stream."""

    path: Path
    duration_seconds: float


def validate_video(path: str | Path) -> VideoFile:
    """Confirm ``path`` is a readable MP4 with a video stream and a duration.

    Filesystem checks run first. ``ffprobe`` then confirms the container has a
    video stream and reports its duration in seconds.
    """
    source = _readable_mp4(path)
    duration = _probe_duration(source)
    return VideoFile(path=source, duration_seconds=duration)


def _readable_mp4(path: str | Path) -> Path:
    """Return a resolved path after the cheap filesystem checks."""
    if not isinstance(path, (str, Path)):
        raise VideoValidationError(
            f"Video path must be a string or Path, got {type(path).__name__}."
        )

    source = Path(path).expanduser()
    if not source.exists():
        raise VideoValidationError(f"Video file does not exist: {source}")
    if not source.is_file():
        raise VideoValidationError(f"Video path is not a file: {source}")
    if source.suffix.lower() != ".mp4":
        raise VideoValidationError(
            f"Expected an .mp4 file, got '{source.name}'."
        )
    if source.stat().st_size == 0:
        raise VideoValidationError(f"Video file is empty: {source}")
    if not os.access(source, os.R_OK):
        raise VideoValidationError(f"Video file is not readable: {source}")

    try:
        with source.open("rb"):
            pass
    except OSError as exc:
        raise VideoValidationError(f"Video file is not readable: {source}") from exc

    return source.resolve()


def _probe_duration(source: Path) -> float:
    """Read the container duration and require at least one video stream."""
    ffprobe = require_binary("ffprobe")
    result = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(source),
        ]
    )
    if result.returncode != 0:
        detail = _command_detail(result.stderr, result.stdout)
        raise VideoValidationError(f"Could not read video '{source}': {detail}")

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise VideoValidationError(
            f"ffprobe returned unreadable metadata for '{source}'."
        ) from exc
    if not isinstance(payload, dict):
        raise VideoValidationError(f"ffprobe returned unreadable metadata for '{source}'.")

    streams = payload.get("streams")
    if not isinstance(streams, list) or not any(
        isinstance(stream, dict) and stream.get("codec_type") == "video"
        for stream in streams
    ):
        raise VideoValidationError(f"No video stream found in '{source}'.")

    duration = _duration_from_probe(payload)
    if duration is None or duration <= 0:
        raise VideoValidationError(f"Could not determine duration of '{source}'.")
    return duration


def _duration_from_probe(payload: dict[str, object]) -> float | None:
    """Prefer the container duration, then the first video stream duration."""
    container = payload.get("format")
    if isinstance(container, dict):
        parsed = _positive_float(container.get("duration"))
        if parsed is not None:
            return parsed

    streams = payload.get("streams")
    if isinstance(streams, list):
        for stream in streams:
            if isinstance(stream, dict) and stream.get("codec_type") == "video":
                parsed = _positive_float(stream.get("duration"))
                if parsed is not None:
                    return parsed
    return None


def _positive_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if number <= 0:
        return None
    return number


def _command_detail(stderr: str, stdout: str) -> str:
    detail = (stderr or stdout or "ffprobe failed").strip()
    if len(detail) > 500:
        return detail[:500] + "..."
    return detail
