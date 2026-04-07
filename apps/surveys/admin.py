from django.contrib import admin

from apps.surveys.models import Survey, SurveySubmission


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ["name", "source", "year", "created_at"]
    list_filter = ["year", "source"]
    search_fields = ["name", "source"]


@admin.register(SurveySubmission)
class SurveySubmissionAdmin(admin.ModelAdmin):
    list_display = ["pk", "survey", "status", "created_at", "processed_at"]
    list_filter = ["status", "survey"]
    search_fields = ["fingerprint"]
    readonly_fields = ["fingerprint", "raw_data"]
