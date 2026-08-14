from django.contrib import admin

from .models import Playlist, PlaylistItem


class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    extra = 1


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "song_count", "is_public", "date_created")
    list_filter = ("is_public", "date_created")
    search_fields = ("name",)
    inlines = [PlaylistItemInline]
