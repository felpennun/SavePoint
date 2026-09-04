from django.urls import path

from accounts.views import CsrfBootstrapView, LoginView, LogoutView, PublicProfileView

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfBootstrapView.as_view(), name="csrf"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profiles/<str:alias>/", PublicProfileView.as_view(), name="public-profile"),
]
