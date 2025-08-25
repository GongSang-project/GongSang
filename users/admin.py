from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username",)}),
        (("사용자 정보"), {"fields": (
            "is_youth",
            "profile_image",
            "is_id_verified",
            "age",
            "gender",
            "phone_number",
            "id_card_image",
            "is_id_card_uploaded",
        )}),
        (("설문 정보"), {"fields": (
            "preferred_time",
            "conversation_style",
            "important_points",
            "meal_preference",
            "weekend_preference",
            "smoking_preference",
            "noise_level",
            "space_sharing_preference",
            "pet_preference",
            "wishes",
        )}),
        (("지역 정보"), {"fields": (
            "interested_province",
            "interested_city",
            "interested_district",
        )}),
        (("동거 정보"), {"fields": (
            "living_type",
            "living_type_other",
        )}),
    )

    list_display = (
        "username",
        "is_youth",
        "is_id_verified",
        "gender",
        "phone_number",
        "is_staff",
    )
    list_filter = ("is_youth", "gender", "is_id_verified", "is_staff")
    search_fields = ("username", "phone_number")
    ordering = ("-date_joined",)