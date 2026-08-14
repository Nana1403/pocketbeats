from django.contrib import admin

from .models import Favorite, ListeningHistory


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "song", "date_saved")
    search_fields = ("user__username", "song__title")


@admin.register(ListeningHistory)
class ListeningHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "song", "playback_position", "time_played")
    search_fields = ("user__username", "song__title")
