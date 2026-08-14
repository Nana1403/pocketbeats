from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SongForm, UploadForm
from .models import Song


def song_payload(song, favorite_ids=None):
    """Serialize a song for the JavaScript player."""
    favorite_ids = favorite_ids or set()
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "genre": song.genre,
        "duration": song.duration,
        "durationDisplay": song.duration_display,
        "audioUrl": song.audio_file.url if song.audio_file else "",
        "coverUrl": song.cover_art.url if song.cover_art else "",
        "isFavorite": song.id in favorite_ids,
    }


@login_required
def library(request):
    """List the current user's songs with optional search."""
    query = request.GET.get("q", "").strip()
    songs = Song.objects.filter(owner=request.user)
    if query:
        songs = songs.filter(
            Q(title__icontains=query)
            | Q(artist__icontains=query)
            | Q(album__icontains=query)
            | Q(genre__icontains=query)
        )
    return render(
        request,
        "music/library.html",
        {"songs": songs, "query": query},
    )


@login_required
def upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save(commit=False)
            song.owner = request.user
            song.save()
            messages.success(request, f"Uploaded “{song.title}”.")
            return redirect("music:library")
    else:
        form = UploadForm()
    return render(request, "music/upload.html", {"form": form})


@login_required
def song_detail(request, pk):
    song = get_object_or_404(Song, pk=pk, owner=request.user)
    return render(request, "music/song_detail.html", {"song": song})


@login_required
def song_edit(request, pk):
    song = get_object_or_404(Song, pk=pk, owner=request.user)
    if request.method == "POST":
        form = SongForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()
            messages.success(request, "Song updated.")
            return redirect("music:song_detail", pk=song.pk)
    else:
        form = SongForm(instance=song)
    return render(request, "music/song_edit.html", {"form": form, "song": song})


@login_required
def song_delete(request, pk):
    song = get_object_or_404(Song, pk=pk, owner=request.user)
    if request.method == "POST":
        title = song.title
        song.delete()
        messages.success(request, f"Deleted “{title}”.")
        return redirect("music:library")
    return render(request, "music/song_confirm_delete.html", {"song": song})


@login_required
def library_json(request):
    """Return the user's songs as JSON for the player queue."""
    from player.models import Favorite

    songs = Song.objects.filter(owner=request.user)
    query = request.GET.get("q", "").strip()
    if query:
        songs = songs.filter(
            Q(title__icontains=query)
            | Q(artist__icontains=query)
            | Q(album__icontains=query)
            | Q(genre__icontains=query)
        )
    favorite_ids = set(
        Favorite.objects.filter(user=request.user).values_list("song_id", flat=True)
    )
    return JsonResponse(
        {"songs": [song_payload(s, favorite_ids) for s in songs]}
    )
