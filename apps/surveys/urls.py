from django.urls import path

from apps.surveys import views

urlpatterns = [
    path("surveys/", views.SurveyListCreateView.as_view(), name="survey-list"),
    path("surveys/<int:pk>/", views.SurveyDetailView.as_view(), name="survey-detail"),
    path("ingest/", views.IngestView.as_view(), name="ingest"),
    path("submissions/", views.SubmissionListView.as_view(), name="submission-list"),
]
