"""Errors raised by ingestion and clipping."""


class GameClipError(Exception):
    """Base error for GameClip AI."""


class VideoValidationError(GameClipError):
    """The input path is missing, unreadable, or not a usable MP4."""


class TimestampError(GameClipError):
    """A start or end timestamp is missing, malformed, or out of range."""


class ClipExtractionError(GameClipError):
    """FFmpeg could not write the requested clip."""
