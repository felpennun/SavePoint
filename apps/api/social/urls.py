from django.urls import path

from social.views import (
    AcceptFriendshipRequestView,
    BlockUserView,
    FriendshipActionView,
    FriendshipCollectionView,
    FriendshipRequestActionView,
    FriendshipRequestCollectionView,
    RelationshipView,
    RejectFriendshipRequestView,
    RemoveFriendshipView,
    SocialSearchView,
    UnblockUserView,
)

app_name = "social"

urlpatterns = [
    path("search/", SocialSearchView.as_view(), name="search"),
    path("requests/", FriendshipRequestCollectionView.as_view(), name="requests"),
    path("requests/<uuid:request_id>/accept/", AcceptFriendshipRequestView.as_view(), name="request-accept"),
    path("requests/<uuid:request_id>/reject/", RejectFriendshipRequestView.as_view(), name="request-reject"),
    path("requests/<uuid:request_id>/<str:action>/", FriendshipRequestActionView.as_view(), name="request-action"),
    path("friendships/", FriendshipCollectionView.as_view(), name="friendships"),
    path("friendships/<str:alias>/remove/", RemoveFriendshipView.as_view(), name="friendship-remove"),
    path("friendships/<str:alias>/block/", BlockUserView.as_view(), name="friendship-block"),
    path("relationships/<str:alias>/", RelationshipView.as_view(), name="relationship"),
    path("blocks/<str:alias>/unblock/", UnblockUserView.as_view(), name="unblock"),
    path("relationships/<str:alias>/<str:action>/", FriendshipActionView.as_view(), name="relationship-action"),
]
