from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        ('개인 정보', {
            'fields': (
                'username',
                'is_youth',
                'profile_image',
                'age',
                'gender',
                'phone_number'
            )
        }),
        ('설문 정보', {
            'fields': (
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
                'interested_province',
                'interested_city',
                'interested_district',
                'living_type',
                'living_type_other'
            )
        }),
    )

    list_display = ('username', 'is_youth', 'age', 'gender', 'phone_number', 'is_id_verified')

    list_filter = ('is_youth', 'is_active', 'is_staff', 'is_superuser', 'is_id_verified', 'gender')
    search_fields = ('username', 'phone_number')