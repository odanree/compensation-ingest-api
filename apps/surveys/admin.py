from django.contrib import admin

from apps.surveys.models import QuoteSource, QuoteSubmission


@admin.register(QuoteSource)
class QuoteSourceAdmin(admin.ModelAdmin):
    list_display = ["name", "installer_name", "quote_year", "created_at"]
    list_filter = ["quote_year"]
    search_fields = ["name", "installer_name"]


@admin.register(QuoteSubmission)
class QuoteSubmissionAdmin(admin.ModelAdmin):
    list_display = ["pk", "quote_source", "status", "created_at", "processed_at"]
    list_filter = ["status", "quote_source"]
    search_fields = ["fingerprint"]
    readonly_fields = ["fingerprint", "raw_data"]
