"""Filesystem and container checks for video ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest

from gameclip.errors import VideoValidationError
from gameclip.ingestion import validate_video


def test_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.mp4"
    with pytest.raises(VideoValidationError, match="does not exist"):
        validate_video(missing)


def test_rejects_directory(tmp_path: Path) -> None:
    folder = tmp_path / "clip.mp4"
    folder.mkdir()
    with pytest.raises(VideoValidationError, match="not a file"):
        validate_video(folder)


def test_rejects_non_mp4(tmp_path: Path) -> None:
    text_file = tmp_path / "notes.txt"
    text_file.write_text("not a video", encoding="utf-8")
    with pytest.raises(VideoValidationError, match="Expected an .mp4"):
        validate_video(text_file)


def test_rejects_empty_mp4(tmp_path: Path) -> None:
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    with pytest.raises(VideoValidationError, match="empty"):
        validate_video(empty)


def test_rejects_unreadable_mp4(tmp_path: Path) -> None:
    locked = tmp_path / "locked.mp4"
    locked.write_bytes(b"not-a-real-video")
    locked.chmod(0)
    try:
        with pytest.raises(VideoValidationError, match="not readable"):
            validate_video(locked)
    finally:
        locked.chmod(0o644)


def test_rejects_file_that_is_not_a_video(tmp_path: Path) -> None:
    fake = tmp_path / "fake.mp4"
    fake.write_bytes(b"this is not an mp4 container")
    with pytest.raises(VideoValidationError, match="Could not read video"):
        validate_video(fake)


def test_accepts_uppercase_suffix_and_reports_duration(sample_mp4: Path, tmp_path: Path) -> None:
    renamed = tmp_path / "SAMPLE.MP4"
    renamed.write_bytes(sample_mp4.read_bytes())

    video = validate_video(renamed)

    assert video.path == renamed.resolve()
    assert video.duration_seconds == pytest.approx(3.0, abs=0.2)


def test_rejects_non_path_value() -> None:
    with pytest.raises(VideoValidationError, match="string or Path"):
        validate_video(12)  # type: ignore[arg-type]
