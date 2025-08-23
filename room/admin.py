from django.contrib import admin
from .models import Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'deposit', 'rent_fee', 'address_province', 'address_city', 'can_short_term', 'created_at', 'is_land_register_verified')
    list_filter = ('can_short_term', 'parking_available', 'pet_allowed', 'is_land_register_verified')
    search_fields = ('owner__username', 'address_city', 'address_district')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('owner', 'contracted_youth')
    fieldsets = (
        ('기본 정보', {
            'fields': ('owner', 'deposit', 'rent_fee', 'floor', 'area', 'utility_fee', 'can_short_term', 'available_date', 'toilet_count')
        }),
        ('주소 및 등기부등본', {
            'fields': ('address_province', 'address_city', 'address_district', 'address_detailed', 'land_register_document', 'is_land_register_verified')
        }),
        ('계약 정보', {
            'fields': ('contracted_youth',)
        }),
        ('시설 및 옵션', {
            'fields': ('options', 'security_facilities', 'other_facilities', 'parking_available', 'pet_allowed', 'heating_type', 'nearest_subway')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at')
        }),
    )