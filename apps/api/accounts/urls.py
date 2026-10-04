from django.urls import path

from accounts.views import (
    CsrfBootstrapView,
    FriendAvatarView,
    FriendCoverView,
    LoginView,
    LogoutView,
    MeView,
    MyAccountDeleteView,
    MyAvatarView,
    MyCoverView,
    MyFavoritesView,
    MyPasswordView,
    MyProfileView,
    MyUsernameView,
    PublicProfileView,
    RegisterView,
    UsernameAvailabilityView,
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
    path("me/avatar/", MyAvatarView.as_view(), name="my-avatar"),
    path("me/cover/", MyCoverView.as_view(), name="my-cover"),
    path("me/password/", MyPasswordView.as_view(), name="my-password"),
    path("me/username/", MyUsernameView.as_view(), name="my-username"),
    path("me/username/availability/", UsernameAvailabilityView.as_view(), name="username-availability"),
    path("me/delete/", MyAccountDeleteView.as_view(), name="my-account-delete"),
    path("profiles/<str:alias>/", PublicProfileView.as_view(), name="public-profile"),
    path("profiles/<str:alias>/avatar/", FriendAvatarView.as_view(), name="friend-avatar"),
    path("profiles/<str:alias>/cover/", FriendCoverView.as_view(), name="friend-cover"),
]
