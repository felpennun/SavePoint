from django.urls import path

from recommendations.views import RecommendationsView

app_name = "recommendations"

urlpatterns = [
    path("genre-taste/", RecommendationsView.as_view(), name="genre-taste"),
]
