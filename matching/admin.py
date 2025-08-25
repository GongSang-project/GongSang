from django.contrib import admin
from .models import MoveInRequest


@admin.register(MoveInRequest)
class MoveInRequestAdmin(admin.ModelAdmin):
    list_display = ("youth", "room", "is_contacted", "requested_at")
    list_filter = ("is_contacted", "requested_at")
    search_fields = ("youth__username", "room__owner__username", "room__id")
    raw_id_fields = ("youth", "room")