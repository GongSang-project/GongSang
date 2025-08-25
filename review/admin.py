from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "target_senior",
        "target_youth",
        "room",
        "satisfaction",
        "re_living_hope",
    )
    list_filter = (
        "satisfaction",
        "re_living_hope",
        "is_anonymous",
        "created_at",
    )
    search_fields = (
        "author__username",
        "target_senior__username",
        "target_youth__username",
        "room__id",
    )
    raw_id_fields = ("author", "target_senior", "target_youth", "room")