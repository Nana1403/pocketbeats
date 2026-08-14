"""Pydantic schemas that validate song metadata before it enters the app.

These are used for cleaning user-entered metadata and, later, for validating
metadata that arrives from an external music API. Keeping validation in one
place means both paths share the same rules.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# A song can plausibly be from the earliest recordings up to next year.
_EARLIEST_YEAR = 1860
_LATEST_YEAR = datetime.now().year + 1


class SongMetadata(BaseModel):
    """Validated, normalized metadata for a single song."""

    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(default="", max_length=200)
    album: str = Field(default="", max_length=200)
    genre: str = Field(default="", max_length=100)
    release_year: int | None = None
    duration: int = Field(default=0, ge=0)

    @field_validator("title", "artist", "album", "genre")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value

    @field_validator("release_year")
    @classmethod
    def _valid_year(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if not (_EARLIEST_YEAR <= value <= _LATEST_YEAR):
            raise ValueError(
                f"release_year must be between {_EARLIEST_YEAR} and {_LATEST_YEAR}"
            )
        return value
