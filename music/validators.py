"""Upload validation helpers for audio files and cover art.

The goal is to *verify* the file rather than trust its name: we check the size,
the extension, and confirm the bytes actually parse as audio using mutagen.
"""

from django.conf import settings
from django.core.exceptions import ValidationError

import mutagen

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".ogg", ".wav", ".flac"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _extension(name: str) -> str:
    dot = name.rfind(".")
    return name[dot:].lower() if dot != -1 else ""


def validate_audio_file(upload):
    """Validate an uploaded audio file's size, extension, and real content."""
    max_size = getattr(settings, "MAX_AUDIO_UPLOAD_SIZE", 25 * 1024 * 1024)
    if upload.size > max_size:
        mb = max_size / (1024 * 1024)
        raise ValidationError(f"Audio file is too large (limit is {mb:.0f} MB).")

    ext = _extension(upload.name)
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise ValidationError(f"Unsupported audio format. Allowed: {allowed}.")

    # Confirm the bytes are really audio, not just a renamed file.
    upload.seek(0)
    try:
        parsed = mutagen.File(upload)
    except Exception:  # mutagen raises a variety of errors on bad input
        parsed = None
    finally:
        upload.seek(0)

    if parsed is None:
        raise ValidationError(
            "This file does not appear to be a valid audio file."
        )


def validate_cover_image(upload):
    """Validate an uploaded cover image's size and extension.

    Pillow (via Django's ImageField) additionally verifies the image content.
    """
    max_size = getattr(settings, "MAX_COVER_UPLOAD_SIZE", 5 * 1024 * 1024)
    if upload.size > max_size:
        mb = max_size / (1024 * 1024)
        raise ValidationError(f"Cover image is too large (limit is {mb:.0f} MB).")

    ext = _extension(upload.name)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise ValidationError(f"Unsupported image format. Allowed: {allowed}.")


def read_audio_duration(upload) -> int:
    """Best-effort read of an audio file's duration in whole seconds."""
    upload.seek(0)
    try:
        parsed = mutagen.File(upload)
        if parsed is not None and parsed.info is not None:
            return int(round(parsed.info.length))
    except Exception:
        pass
    finally:
        upload.seek(0)
    return 0
