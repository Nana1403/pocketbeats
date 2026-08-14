from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Per-user preferences, such as the chosen player theme."""

    class Theme(models.TextChoices):
        BUBBLEGUM = "bubblegum", "Bubblegum Pop"
        RETRO = "retro", "Retro Silver"
        MIDNIGHT = "midnight", "Midnight"
        NATURE = "nature", "Nature Mix"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    theme = models.CharField(
        max_length=20, choices=Theme.choices, default=Theme.BUBBLEGUM
    )
    display_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Profile for {self.user}"
