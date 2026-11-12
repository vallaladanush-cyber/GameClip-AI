"""Parse clip start and end times."""

from __future__ import annotations

import math
import re

from gameclip.errors import TimestampError

# "1:30", "1:30.5", or "01:02:03.25". A bare number of seconds is handled separately.
_CLOCK_TIME = re.compile(r"^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$")
_SECONDS = re.compile(r"^\d+(?:\.\d+)?$")


def parse_timestamp(value: str | float) -> float:
    """Convert seconds or a clock time to seconds.

    Accepted forms are ``12``, ``12.5``, ``1:30``, ``1:30.5``, and ``01:02:03``.
    """
    if isinstance(value, bool):
        raise TimestampError("Timestamp must be seconds or a clock time, not a boolean.")

    if isinstance(value, (int, float)):
        seconds = float(value)
    elif isinstance(value, str):
        seconds = _parse_text(value)
    else:
        raise TimestampError(
            f"Timestamp must be seconds or a clock time, got {type(value).__name__}."
        )

    if not math.isfinite(seconds):
        raise TimestampError("Timestamp must be a finite number of seconds.")
    if seconds < 0:
        raise TimestampError("Timestamp cannot be negative.")
    return seconds


def validate_range(start: float, end: float, duration_seconds: float) -> None:
    """Require ``0 <= start < end`` and ``end`` inside the source duration.

    A 50 ms tolerance covers container durations that round slightly short of
    the requested end time.
    """
    if start >= end:
        raise TimestampError(
            f"End time ({end:.3f}s) must be later than start time ({start:.3f}s)."
        )
    if start > duration_seconds:
        raise TimestampError(
            f"Start time ({start:.3f}s) is past the end of the video "
            f"({duration_seconds:.3f}s)."
        )
    if end > duration_seconds + 0.05:
        raise TimestampError(
            f"End time ({end:.3f}s) is beyond the video duration "
            f"({duration_seconds:.3f}s)."
        )


def _parse_text(value: str) -> float:
    text = value.strip()
    if not text:
        raise TimestampError("Timestamp is empty.")
    if _SECONDS.fullmatch(text):
        return float(text)

    match = _CLOCK_TIME.fullmatch(text)
    if match is None:
        raise TimestampError(
            f"Cannot parse timestamp {value!r}. Use seconds (12.5) or clock time (HH:MM:SS)."
        )

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    if minutes >= 60 or seconds >= 60:
        raise TimestampError(
            f"Clock time {value!r} has minutes or seconds outside 0-59."
        )
    return hours * 3600 + minutes * 60 + seconds
