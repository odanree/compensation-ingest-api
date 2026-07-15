from django.contrib import admin

from apps.compensation.models import Location, SolarQuote, SystemConfig


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ["panel_brand", "panel_tier_label", "panel_tier", "tier_order"]
    list_filter = ["panel_tier"]
    search_fields = ["panel_brand", "panel_tier_label"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["raw_location", "city", "state", "country", "metro"]
    list_filter = ["country", "state"]
    search_fields = ["raw_location", "city", "metro"]


@admin.register(SolarQuote)
class SolarQuoteAdmin(admin.ModelAdmin):
    list_display = [
        "submission",
        "system_config",
        "location",
        "system_size_band",
        "cost_per_watt",
        "system_cost",
        "installer_type",
        "created_at",
    ]
    list_filter = ["system_size_band", "installer_type", "system_config__panel_tier"]
    search_fields = ["location__city", "location__state", "system_config__panel_brand"]
    select_related = ["system_config", "location", "submission"]
