from django.urls import path

from accounts.views import CsrfBootstrapView, LoginView, LogoutView

app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfBootstrapView.as_view(), name="csrf"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
