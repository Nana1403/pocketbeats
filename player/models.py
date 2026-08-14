from django.conf import settings
from django.db import models


class Favorite(models.Model):
    """A song a user has marked as a favorite."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    song = models.ForeignKey(
        "music.Song",
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    date_saved = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_saved"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "song"], name="unique_favorite_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.song}"


class ListeningHistory(models.Model):
    """A record that a user played a song, with the last playback position."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="history",
    )
    song = models.ForeignKey(
        "music.Song",
        on_delete=models.CASCADE,
        related_name="plays",
    )
    time_played = models.DateTimeField(auto_now=True)
    # Position in seconds where the user last was (for "continue listening").
    playback_position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-time_played"]
        verbose_name_plural = "Listening history"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "song"], name="unique_history_per_user_song"
            )
        ]

    def __str__(self):
        return f"{self.user} played {self.song}"
