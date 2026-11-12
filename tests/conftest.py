"""Shared fixtures. The sample MP4 is generated with FFmpeg, not client footage."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_mp4(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Three-second synthetic MP4 used by clipping tests."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.fail("ffmpeg is required. Install it with: brew install ffmpeg")

    destination = tmp_path_factory.mktemp("media") / "sample.mp4"
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=320x240:rate=30:duration=3",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:sample_rate=44100:duration=3",
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(destination),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return destination
