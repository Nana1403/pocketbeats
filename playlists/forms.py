from django import forms

from .models import Playlist


class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ["name", "cover_image", "is_public"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Playlist name"}),
        }
