from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'target_senior', 'target_youth', 'room', 'lived_period', 'satisfaction', 're_living_hope', 'is_anonymous', 'created_at')
    list_filter = ('lived_period', 'satisfaction', 're_living_hope', 'is_anonymous', 'created_at')
    search_fields = ('author__username', 'target_senior__username', 'target_youth__username', 'room__id')
    raw_id_fields = ('author', 'target_senior', 'target_youth', 'room')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('후기 정보', {
            'fields': ('author', 'target_senior', 'target_youth', 'room', 'lived_period', 'satisfaction', 're_living_hope', 'is_anonymous', 'contract_document')
        }),
        ('상세 후기', {
            'fields': ('good_points', 'bad_points')
        }),
        ('메타 정보', {
            'fields': ('created_at',)
        }),
    )