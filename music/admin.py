from django.contrib import admin

from .models import Song


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "album", "owner", "duration_display", "date_uploaded")
    list_filter = ("genre", "date_uploaded")
    search_fields = ("title", "artist", "album", "genre")
    readonly_fields = ("duration", "date_uploaded")
