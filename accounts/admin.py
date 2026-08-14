from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "display_name")
    list_filter = ("theme",)
    search_fields = ("user__username", "display_name")
