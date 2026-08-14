from django import forms
from pydantic import ValidationError as PydanticValidationError

from .models import Song
from .schemas import SongMetadata
from .validators import (
    read_audio_duration,
    validate_audio_file,
    validate_cover_image,
)


class SongForm(forms.ModelForm):
    """Create/edit a song. Audio is required on create, optional on edit."""

    class Meta:
        model = Song
        fields = [
            "title",
            "artist",
            "album",
            "genre",
            "release_year",
            "audio_file",
            "cover_art",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Song title"}),
            "artist": forms.TextInput(attrs={"placeholder": "Artist"}),
            "album": forms.TextInput(attrs={"placeholder": "Album"}),
            "genre": forms.TextInput(attrs={"placeholder": "Genre"}),
            "release_year": forms.NumberInput(attrs={"placeholder": "Year"}),
        }

    def clean_audio_file(self):
        upload = self.cleaned_data.get("audio_file")
        # On edit the file may be unchanged (already a stored file, not re-uploaded).
        if upload and hasattr(upload, "size"):
            validate_audio_file(upload)
        return upload

    def clean_cover_art(self):
        upload = self.cleaned_data.get("cover_art")
        if upload and hasattr(upload, "size"):
            validate_cover_image(upload)
        return upload

    def clean(self):
        """Normalize metadata through the shared Pydantic schema."""
        cleaned = super().clean()
        try:
            validated = SongMetadata(
                title=cleaned.get("title") or "",
                artist=cleaned.get("artist") or "",
                album=cleaned.get("album") or "",
                genre=cleaned.get("genre") or "",
                release_year=cleaned.get("release_year"),
            )
        except PydanticValidationError as exc:
            # Surface the first error against a sensible field.
            first = exc.errors()[0]
            field = first["loc"][0] if first.get("loc") else None
            message = first.get("msg", "Invalid metadata.")
            if field in self.fields:
                self.add_error(field, message)
            else:
                self.add_error(None, message)
            return cleaned

        cleaned["title"] = validated.title
        cleaned["artist"] = validated.artist
        cleaned["album"] = validated.album
        cleaned["genre"] = validated.genre
        cleaned["release_year"] = validated.release_year
        return cleaned

    def save(self, commit=True):
        song = super().save(commit=False)
        # Fill in duration from the uploaded audio when we have a fresh file.
        upload = self.cleaned_data.get("audio_file")
        if upload and hasattr(upload, "size"):
            song.duration = read_audio_duration(upload)
        if commit:
            song.save()
        return song


class UploadForm(SongForm):
    """Upload form: adds the required rights-confirmation agreement."""

    agree_rights = forms.BooleanField(
        required=True,
        label="I own this music or have permission to upload and use it.",
    )
