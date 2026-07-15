from django.urls import path

from apps.surveys import views

urlpatterns = [
    path("quote-sources/", views.QuoteSourceListCreateView.as_view(), name="quote-source-list"),
    path("quote-sources/<int:pk>/", views.QuoteSourceDetailView.as_view(), name="quote-source-detail"),
    path("ingest/", views.IngestView.as_view(), name="ingest"),
    path("submissions/", views.QuoteSubmissionListView.as_view(), name="submission-list"),
]
