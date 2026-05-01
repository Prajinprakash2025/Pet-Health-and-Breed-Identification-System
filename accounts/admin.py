from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "city", "country", "created_at")
    list_filter = ("city", "country", "created_at")
    search_fields = ("user__username", "user__email", "phone_number", "city", "country")
