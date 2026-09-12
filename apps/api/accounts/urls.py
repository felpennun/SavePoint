from django.urls import path

from accounts.views import (
    CsrfBootstrapView,
    LoginView,
    LogoutView,
    MeView,
    MyFavoritesView,
    MyProfileView,
    PublicProfileView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfBootstrapView.as_view(), name="csrf"),
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("me/profile/", MyProfileView.as_view(), name="my-profile"),
    path("me/favorites/", MyFavoritesView.as_view(), name="my-favorites"),
    path("profiles/<str:alias>/", PublicProfileView.as_view(), name="public-profile"),
]
