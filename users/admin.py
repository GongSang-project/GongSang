# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_youth', 'is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('개인 정보', {'fields': ('first_name', 'last_name', 'email', 'is_youth', 'profile_image', 'is_id_verified', 'age', 'gender', 'affiliation', 'introduction')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('중요 날짜', {'fields': ('last_login', 'date_joined')}),

        ('생활 습관 설문', {'fields': (
            'preferred_time',
            'conversation_style',
            'important_points',
            'meal_preference',
            'weekend_preference',
            'smoking_preference',
            'noise_level',
            'space_sharing_preference',
            'pet_preference',
            'wishes',
        )}),
    )