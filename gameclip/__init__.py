"""GameClip AI: cut short clips from authorised gameplay recordings."""

from gameclip.clipping import extract_clip
from gameclip.errors import (
    ClipExtractionError,
    GameClipError,
    TimestampError,
    VideoValidationError,
)
from gameclip.ingestion import VideoFile, validate_video

__all__ = [
    "ClipExtractionError",
    "GameClipError",
    "TimestampError",
    "VideoFile",
    "VideoValidationError",
    "extract_clip",
    "validate_video",
]

__version__ = "0.1.0"
