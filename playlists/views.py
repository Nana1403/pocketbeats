from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from music.models import Song
from music.views import song_payload

from .forms import PlaylistForm
from .models import Playlist, PlaylistItem


@login_required
def playlist_list(request):
    playlists = Playlist.objects.filter(owner=request.user)
    return render(request, "playlists/list.html", {"playlists": playlists})


@login_required
def playlist_create(request):
    if request.method == "POST":
        form = PlaylistForm(request.POST, request.FILES)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.owner = request.user
            playlist.save()
            messages.success(request, f"Created playlist “{playlist.name}”.")
            return redirect("playlists:detail", pk=playlist.pk)
    else:
        form = PlaylistForm()
    return render(request, "playlists/form.html", {"form": form, "creating": True})


@login_required
def playlist_detail(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    items = playlist.items.select_related("song")
    # Songs the user owns that aren't already in this playlist (for the add menu).
    in_playlist = items.values_list("song_id", flat=True)
    available = Song.objects.filter(owner=request.user).exclude(id__in=in_playlist)
    return render(
        request,
        "playlists/detail.html",
        {"playlist": playlist, "items": items, "available": available},
    )


@login_required
def playlist_edit(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PlaylistForm(request.POST, request.FILES, instance=playlist)
        if form.is_valid():
            form.save()
            messages.success(request, "Playlist updated.")
            return redirect("playlists:detail", pk=playlist.pk)
    else:
        form = PlaylistForm(instance=playlist)
    return render(
        request,
        "playlists/form.html",
        {"form": form, "creating": False, "playlist": playlist},
    )


@login_required
def playlist_delete(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    if request.method == "POST":
        name = playlist.name
        playlist.delete()
        messages.success(request, f"Deleted playlist “{name}”.")
        return redirect("playlists:list")
    return render(request, "playlists/confirm_delete.html", {"playlist": playlist})


@login_required
@require_POST
def add_song(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    song = get_object_or_404(Song, pk=request.POST.get("song"), owner=request.user)
    next_position = (
        playlist.items.aggregate(m=Max("position"))["m"] or 0
    ) + 1
    PlaylistItem.objects.get_or_create(
        playlist=playlist, song=song, defaults={"position": next_position}
    )
    messages.success(request, f"Added “{song.title}”.")
    return redirect("playlists:detail", pk=playlist.pk)


@login_required
@require_POST
def remove_song(request, pk, song_id):
    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    PlaylistItem.objects.filter(playlist=playlist, song_id=song_id).delete()
    messages.success(request, "Removed from playlist.")
    return redirect("playlists:detail", pk=playlist.pk)


@login_required
def playlist_json(request, pk):
    """Return a playlist's songs in order for the player."""
    from player.models import Favorite

    playlist = get_object_or_404(Playlist, pk=pk, owner=request.user)
    favorite_ids = set(
        Favorite.objects.filter(user=request.user).values_list("song_id", flat=True)
    )
    songs = playlist.ordered_songs()
    return JsonResponse(
        {
            "name": playlist.name,
            "songs": [song_payload(s, favorite_ids) for s in songs],
        }
    )
