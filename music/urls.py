from django.urls import path

from . import views

app_name = "music"

urlpatterns = [
    path("", views.library, name="library"),
    path("upload/", views.upload, name="upload"),
    path("api/songs/", views.library_json, name="library_json"),
    path("<int:pk>/", views.song_detail, name="song_detail"),
    path("<int:pk>/edit/", views.song_edit, name="song_edit"),
    path("<int:pk>/delete/", views.song_delete, name="song_delete"),
]
