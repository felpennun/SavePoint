from django.urls import path

from catalogue.views import GameDetailView, GameListView, SourcesView

app_name = "catalogue"

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/<slug:slug>/", GameDetailView.as_view(), name="game-detail"),
    path("sources/", SourcesView.as_view(), name="sources"),
]
