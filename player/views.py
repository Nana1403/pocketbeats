import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from music.models import Song
from music.views import song_payload

from .models import Favorite, ListeningHistory


@login_required
@require_POST
def toggle_favorite(request, pk):
    """Add or remove a song from the user's favorites. Returns JSON."""
    song = get_object_or_404(Song, pk=pk, owner=request.user)
    favorite, created = Favorite.objects.get_or_create(user=request.user, song=song)
    if not created:
        favorite.delete()
        return JsonResponse({"isFavorite": False})
    return JsonResponse({"isFavorite": True})


@login_required
@require_POST
def record_play(request, pk):
    """Record that the user played a song, storing the playback position."""
    song = get_object_or_404(Song, pk=pk, owner=request.user)
    position = 0
    if request.body:
        try:
            position = int(json.loads(request.body).get("position", 0))
        except (ValueError, json.JSONDecodeError):
            position = 0

    history, _ = ListeningHistory.objects.get_or_create(
        user=request.user, song=song
    )
    history.playback_position = max(0, position)
    history.save()  # auto_now updates time_played
    return JsonResponse({"ok": True})


@login_required
def recently_played(request):
    history = (
        ListeningHistory.objects.filter(user=request.user)
        .select_related("song")[:50]
    )
    return render(request, "player/recently_played.html", {"history": history})


@login_required
def favorites(request):
    favs = (
        Favorite.objects.filter(user=request.user).select_related("song")
    )
    return render(request, "player/favorites.html", {"favorites": favs})


@login_required
def favorites_json(request):
    favorite_ids = set(
        Favorite.objects.filter(user=request.user).values_list("song_id", flat=True)
    )
    songs = Song.objects.filter(id__in=favorite_ids)
    return JsonResponse(
        {"songs": [song_payload(s, favorite_ids) for s in songs]}
    )
