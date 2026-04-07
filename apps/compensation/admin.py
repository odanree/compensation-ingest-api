from django.contrib import admin

from apps.compensation.models import CompensationRecord, Location, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["title", "normalized_title", "family"]
    list_filter = ["family"]
    search_fields = ["title", "normalized_title"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["raw_location", "city", "state", "country", "metro"]
    list_filter = ["country"]
    search_fields = ["raw_location", "city", "metro"]


@admin.register(CompensationRecord)
class CompensationRecordAdmin(admin.ModelAdmin):
    list_display = ["role", "location", "level", "total_comp", "base_salary", "company_size", "created_at"]
    list_filter = ["company_size", "level", "role__family"]
    search_fields = ["role__normalized_title", "location__city"]
    select_related = ["role", "location", "submission"]
