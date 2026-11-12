"""Locate FFmpeg binaries and run them."""

from __future__ import annotations

import shutil
import subprocess

from gameclip.errors import GameClipError


def require_binary(name: str) -> str:
    """Return the absolute path of an FFmpeg tool, or raise if it is missing."""
    path = shutil.which(name)
    if path is None:
        raise GameClipError(
            f"{name} was not found on PATH. Install FFmpeg with: brew install ffmpeg"
        )
    return path


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and capture stdout and stderr as text."""
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise GameClipError(f"Could not run '{command[0]}': {exc}") from exc
