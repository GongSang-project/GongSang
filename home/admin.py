from django.contrib import admin
from .models import Region, Listing


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "region")
    list_filter = ("region",)
    search_fields = ("title", "description")