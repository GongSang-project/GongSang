from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'target_youth', 'target_senior', 'room', 'created_at')

    list_filter = ('is_anonymous', 'satisfaction', 'lived_period', 'created_at')

    search_fields = ('author__username', 'target_youth__username', 'room__address')

    readonly_fields = ('created_at',)
    fieldsets = (
        ('기본 정보', {
            'fields': ('author', 'target_youth', 'target_senior', 'room', 'is_anonymous', 'created_at')
        }),
        ('후기 내용', {
            'fields': ('lived_period', 'satisfaction', 'good_points', 'bad_points', 're_living_hope')
        }),
        ('계약서', {
            'fields': ('contract_document',)
        }),
    )