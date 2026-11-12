"""Timestamp parsing and range checks."""

from __future__ import annotations

import pytest

from gameclip.errors import TimestampError
from gameclip.timestamps import parse_timestamp, validate_range


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0.0),
        (12.5, 12.5),
        ("90", 90.0),
        (" 12.5 ", 12.5),
        ("1:30", 90.0),
        ("1:30.5", 90.5),
        ("01:02:03", 3723.0),
        ("01:02:03.25", 3723.25),
    ],
)
def test_parse_timestamp(value: str | float, expected: float) -> None:
    assert parse_timestamp(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", ["", "   ", "1:60", "abc", "1:2:3:4", -1, float("nan")])
def test_parse_timestamp_rejects_bad_values(value: str | float) -> None:
    with pytest.raises(TimestampError):
        parse_timestamp(value)


def test_range_rejects_end_before_start() -> None:
    with pytest.raises(TimestampError, match="later than start"):
        validate_range(2.0, 2.0, duration_seconds=10.0)


def test_range_rejects_end_past_duration() -> None:
    with pytest.raises(TimestampError, match="beyond"):
        validate_range(0.0, 10.2, duration_seconds=10.0)


def test_range_allows_small_duration_rounding() -> None:
    validate_range(0.0, 10.04, duration_seconds=10.0)
