from django.contrib import admin
from .models import Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'address', 'owner', 'rent_fee', 'deposit', 'can_short_term', 'created_at')
    list_display_links = ('address', 'owner',)
    list_filter = ('can_short_term', 'created_at',)
    search_fields = ('address', 'owner__username',)
    raw_id_fields = ('owner', 'contracted_youth',)
    fieldsets = (
        ('기본 정보', {'fields': ('deposit', 'rent_fee', 'address', 'floor', 'area', 'utility_fee')}),
        ('추가 정보', {'fields': ('can_short_term', 'toilet_count', 'available_date')}),
        ('소유주 및 계약 정보', {'fields': ('owner', 'contracted_youth')}),
        ('집 주인 정보', {'fields': ('owner_living_status',)}),
        ('AI 분석 결과', {'fields': ('ai_analysis_result1', 'ai_analysis_result2', 'ai_matching_score')}),
        ('시설 및 주변 정보', {'fields': ('options', 'security_facilities', 'nearest_subway')}),
    )
    readonly_fields = ('created_at', 'updated_at')