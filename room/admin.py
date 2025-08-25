from django.contrib import admin
from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "address_city",
        "rent_fee",
        "can_short_term",
        "parking_available",
        "pet_allowed",
        "created_at",
    )
    list_filter = (
        "can_short_term",
        "parking_available",
        "pet_allowed",
        "heating_type",
    )
    search_fields = (
        "owner__username",
        "address_city",
        "address_detailed",
    )
    raw_id_fields = ("owner", "contracted_youth")