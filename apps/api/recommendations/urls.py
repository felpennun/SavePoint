from django.urls import path

from recommendations.views import ContentRecsView, RecommendationSnapshotView, RecommendationsView

app_name = "recommendations"

urlpatterns = [
    path("genre-taste/", RecommendationsView.as_view(), name="genre-taste"),
    path("content/", ContentRecsView.as_view(), name="content"),
    path("snapshot/", RecommendationSnapshotView.as_view(), name="snapshot"),
]
