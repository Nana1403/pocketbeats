from django.shortcuts import render


def home(request):
    """Landing page hosting the MP3-player interface.

    Signed-in users get their own library loaded into the player; everyone
    can try the player with a bundled sample track (Version 1 behaviour).
    """
    context = {}
    if request.user.is_authenticated:
        context["song_count"] = request.user.songs.count()
        context["playlist_count"] = request.user.playlists.count()
    return render(request, "core/home.html", context)
