from django.urls import path

from catalogue.views import (
    GameDetailView,
    GameListView,
    NewReleasesView,
    OwnedGamesDlcView,
    SourcesView,
)

app_name = "catalogue"

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/<slug:slug>/", GameDetailView.as_view(), name="game-detail"),
    path("new-releases/", NewReleasesView.as_view(), name="new-releases"),
    path("owned-dlc/", OwnedGamesDlcView.as_view(), name="owned-dlc"),
    path("sources/", SourcesView.as_view(), name="sources"),
]
