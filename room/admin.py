from django.contrib import admin
from .models import Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'get_full_address', 'owner', 'rent_fee', 'deposit', 'can_short_term', 'parking_available', 'pet_allowed',
    'heating_type', 'created_at')
    list_display_links = ('get_full_address', 'owner',)
    list_filter = ('can_short_term', 'parking_available', 'pet_allowed', 'heating_type', 'created_at',)
    search_fields = ('address_province', 'address_city', 'address_district', 'address_detailed', 'owner__username',)
    raw_id_fields = ('owner', 'contracted_youth',)
    fieldsets = (
        ('기본 정보', {'fields': ('deposit', 'rent_fee', 'floor', 'area', 'utility_fee')}),
        ('주소 정보', {'fields': ('address_province', 'address_city', 'address_district', 'address_detailed')}),
        ('추가 정보', {'fields': ('can_short_term', 'toilet_count', 'available_date')}),
        ('소유주 및 계약 정보', {'fields': ('owner', 'contracted_youth')}),
        ('집 주인 정보', {'fields': ('owner_living_status',)}),
        ('시설 정보', {'fields': (
        'options', 'security_facilities', 'other_facilities', 'parking_available', 'pet_allowed', 'heating_type')}),
        ('주변 정보', {'fields': ('nearest_subway',)}),
    )
    readonly_fields = ('created_at', 'updated_at')

    # 여러 주소 필드를 합쳐서 하나의 문자열로 반환하는 메서드
    def get_full_address(self, obj):
        return f"{obj.address_province} {obj.address_city} {obj.address_district} {obj.address_detailed}"

    get_full_address.short_description = '주소'