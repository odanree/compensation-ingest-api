from django.urls import path

from apps.compensation import views

urlpatterns = [
    path("compensation/", views.CompensationRecordListView.as_view(), name="compensation-list"),
    path("compensation/summary/", views.CompensationSummaryView.as_view(), name="compensation-summary"),
]
