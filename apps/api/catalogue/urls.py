from django.urls import path

from catalogue.views import GameDetailView, GameListView

app_name = "catalogue"

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/<slug:slug>/", GameDetailView.as_view(), name="game-detail"),
]
