"""Cut a time range out of a validated MP4 with FFmpeg."""

from __future__ import annotations

from pathlib import Path

from gameclip.errors import ClipExtractionError, TimestampError
from gameclip.ingestion import VideoFile, validate_video
from gameclip.media import require_binary, run_command
from gameclip.timestamps import parse_timestamp, validate_range


def extract_clip(
    source: str | Path | VideoFile,
    start: str | float,
    end: str | float,
    output_dir: str | Path = "output",
    filename: str | None = None,
) -> Path:
    """Cut ``[start, end)`` from ``source`` and save an MP4 in ``output_dir``.

    The clip is re-encoded (H.264 + AAC) so the cut starts on the requested
    time instead of the previous keyframe. ``-ss`` is placed before ``-i`` so
    FFmpeg seeks before decoding. Audio is included only when the source has it.

    Returns the path of the written MP4. An existing file at that path is replaced.
    """
    video = source if isinstance(source, VideoFile) else validate_video(source)
    start_seconds = parse_timestamp(start)
    end_seconds = parse_timestamp(end)
    validate_range(start_seconds, end_seconds, video.duration_seconds)

    destination = _destination(video.path, output_dir, filename, start_seconds, end_seconds)
    duration = min(end_seconds, video.duration_seconds) - start_seconds
    if duration <= 0:
        raise TimestampError("Clip duration must be greater than zero.")

    _encode_clip(video.path, destination, start_seconds, duration)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise ClipExtractionError(f"FFmpeg did not write a clip to '{destination}'.")
    return destination


def _encode_clip(source: Path, destination: Path, start: float, duration: float) -> None:
    ffmpeg = require_binary("ffmpeg")
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    result = run_command(command)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ffmpeg failed").strip()
        if len(detail) > 500:
            detail = detail[:500] + "..."
        destination.unlink(missing_ok=True)
        raise ClipExtractionError(f"FFmpeg failed to extract the clip: {detail}")


def _destination(
    source: Path,
    output_dir: str | Path,
    filename: str | None,
    start: float,
    end: float,
) -> Path:
    if not isinstance(output_dir, (str, Path)):
        raise ClipExtractionError(
            f"Output directory must be a string or Path, got {type(output_dir).__name__}."
        )

    directory = Path(output_dir).expanduser()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ClipExtractionError(f"Could not create output directory '{directory}': {exc}") from exc
    if not directory.is_dir():
        raise ClipExtractionError(f"Output path is not a directory: {directory}")

    name = filename if filename is not None else _default_name(source, start, end)
    _reject_unsafe_filename(name)

    destination = (directory / name).resolve()
    resolved_directory = directory.resolve()
    if destination.parent != resolved_directory:
        raise ClipExtractionError(f"Output filename escapes the output directory: {name}")
    return destination


def _default_name(source: Path, start: float, end: float) -> str:
    return f"{source.stem}_{start:.2f}-{end:.2f}.mp4"


def _reject_unsafe_filename(filename: str) -> None:
    if not isinstance(filename, str) or not filename.strip():
        raise ClipExtractionError("Output filename must be a non-empty string.")
    candidate = Path(filename)
    if candidate.name != filename or filename in {".", ".."}:
        raise ClipExtractionError(
            f"Output filename must be a file name, not a path: {filename!r}"
        )
    if candidate.suffix.lower() != ".mp4":
        raise ClipExtractionError(f"Output filename must end in .mp4, got {filename!r}.")
