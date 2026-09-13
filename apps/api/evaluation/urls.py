from django.urls import path

from evaluation.views import (
    ResearchArtifactsView,
    ResearchComparisonView,
    ResearchExportsView,
    ResearchRunsView,
)


app_name = "evaluation"

urlpatterns = [
    path("runs/", ResearchRunsView.as_view(), name="runs"),
    path("comparison/", ResearchComparisonView.as_view(), name="comparison"),
    path("artifacts/", ResearchArtifactsView.as_view(), name="artifacts"),
    path("exports/", ResearchExportsView.as_view(), name="exports"),
]
