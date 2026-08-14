from django.urls import path

from . import views

app_name = "player"

urlpatterns = [
    path("favorites/", views.favorites, name="favorites"),
    path("recently-played/", views.recently_played, name="recently_played"),
    path("api/favorites/", views.favorites_json, name="favorites_json"),
    path("api/favorite/<int:pk>/", views.toggle_favorite, name="toggle_favorite"),
    path("api/play/<int:pk>/", views.record_play, name="record_play"),
]
