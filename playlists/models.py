from django.conf import settings
from django.db import models
from django.urls import reverse


def playlist_cover_upload_to(instance, filename):
    from music.models import _unique_name  # reuse the safe-name helper

    return f"covers/playlists/{instance.owner_id}/{_unique_name(filename)}"


class Playlist(models.Model):
    """An ordered, user-owned collection of songs."""

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="playlists",
    )
    songs = models.ManyToManyField(
        "music.Song",
        through="PlaylistItem",
        related_name="playlists",
        blank=True,
    )
    cover_image = models.ImageField(
        upload_to=playlist_cover_upload_to, null=True, blank=True
    )
    is_public = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("playlists:detail", args=[self.pk])

    @property
    def song_count(self) -> int:
        return self.items.count()

    def ordered_songs(self):
        """Return the songs in playlist order."""
        return [item.song for item in self.items.select_related("song")]


class PlaylistItem(models.Model):
    """Through model that keeps songs ordered within a playlist."""

    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, related_name="items"
    )
    song = models.ForeignKey(
        "music.Song", on_delete=models.CASCADE, related_name="playlist_items"
    )
    position = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "date_added"]
        constraints = [
            models.UniqueConstraint(
                fields=["playlist", "song"], name="unique_song_per_playlist"
            )
        ]

    def __str__(self):
        return f"{self.song} in {self.playlist}"
