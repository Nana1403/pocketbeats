import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse


def _unique_name(original_name: str) -> str:
    """Return a safe, unique filename that keeps the original extension."""
    suffix = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


def audio_upload_to(instance, filename):
    """Store audio under media/audio/<user_id>/<uuid>.<ext>."""
    return f"audio/{instance.owner_id}/{_unique_name(filename)}"


def cover_upload_to(instance, filename):
    """Store artwork under media/covers/<user_id>/<uuid>.<ext>."""
    return f"covers/{instance.owner_id}/{_unique_name(filename)}"


class Song(models.Model):
    """A single piece of audio owned by a user."""

    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200, blank=True)
    album = models.CharField(max_length=200, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    release_year = models.PositiveIntegerField(null=True, blank=True)

    audio_file = models.FileField(upload_to=audio_upload_to)
    cover_art = models.ImageField(upload_to=cover_upload_to, null=True, blank=True)

    duration = models.PositiveIntegerField(default=0, help_text="Length in seconds")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="songs",
    )
    date_uploaded = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_uploaded"]
        indexes = [
            models.Index(fields=["owner", "title"]),
        ]

    def __str__(self):
        label = self.title
        if self.artist:
            label = f"{self.artist} — {self.title}"
        return label

    def get_absolute_url(self):
        return reverse("music:song_detail", args=[self.pk])

    @property
    def duration_display(self) -> str:
        """Return the duration formatted as M:SS."""
        minutes, seconds = divmod(int(self.duration or 0), 60)
        return f"{minutes}:{seconds:02d}"
