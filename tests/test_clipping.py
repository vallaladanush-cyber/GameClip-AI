"""FFmpeg clip extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from gameclip.__main__ import main
from gameclip.clipping import extract_clip
from gameclip.errors import ClipExtractionError, TimestampError
from gameclip.ingestion import validate_video


def test_extract_clip_writes_one_second_mp4(sample_mp4: Path, tmp_path: Path) -> None:
    output_dir = tmp_path / "clips"

    clip = extract_clip(sample_mp4, start="0:00.5", end="0:01.5", output_dir=output_dir)

    assert clip == output_dir / "sample_0.50-1.50.mp4"
    assert clip.is_file()
    assert clip.stat().st_size > 0
    info = validate_video(clip)
    assert info.duration_seconds == pytest.approx(1.0, abs=0.25)


def test_extract_clip_rejects_range_past_the_end(sample_mp4: Path, tmp_path: Path) -> None:
    with pytest.raises(TimestampError, match="beyond"):
        extract_clip(sample_mp4, start=0, end=30, output_dir=tmp_path)


def test_extract_clip_rejects_path_as_filename(sample_mp4: Path, tmp_path: Path) -> None:
    with pytest.raises(ClipExtractionError, match="not a path"):
        extract_clip(
            sample_mp4,
            start=0,
            end=1,
            output_dir=tmp_path,
            filename="../escape.mp4",
        )


def test_extract_clip_rejects_non_mp4_filename(sample_mp4: Path, tmp_path: Path) -> None:
    with pytest.raises(ClipExtractionError, match=r"\.mp4"):
        extract_clip(
            sample_mp4,
            start=0,
            end=1,
            output_dir=tmp_path,
            filename="clip.mov",
        )


def test_cli_writes_named_clip(sample_mp4: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            str(sample_mp4),
            "0",
            "1",
            "-o",
            str(tmp_path),
            "-n",
            "intro.mp4",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    written = Path(captured.out.strip())
    assert written == tmp_path / "intro.mp4"
    assert written.is_file()


def test_cli_reports_validation_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(tmp_path / "missing.mp4"), "0", "1"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
