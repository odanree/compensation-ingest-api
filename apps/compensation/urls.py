from django.urls import path

from apps.compensation import views

urlpatterns = [
    path("quotes/", views.SolarQuoteListView.as_view(), name="solar-quote-list"),
    path("quotes/summary/", views.CostSummaryView.as_view(), name="cost-summary"),
]
