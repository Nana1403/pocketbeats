from django.urls import path

from . import views

app_name = "playlists"

urlpatterns = [
    path("", views.playlist_list, name="list"),
    path("new/", views.playlist_create, name="create"),
    path("<int:pk>/", views.playlist_detail, name="detail"),
    path("<int:pk>/edit/", views.playlist_edit, name="edit"),
    path("<int:pk>/delete/", views.playlist_delete, name="delete"),
    path("<int:pk>/add/", views.add_song, name="add_song"),
    path("<int:pk>/remove/<int:song_id>/", views.remove_song, name="remove_song"),
    path("<int:pk>/api/songs/", views.playlist_json, name="playlist_json"),
]
