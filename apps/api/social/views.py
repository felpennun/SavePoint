"""Authenticated HTTP boundary for social commands and exact discovery."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from social import services
from social.serializers import (
    ExactAliasSerializer,
    RecommendationInputSerializer,
    SocialAliasRequestSerializer,
    serialize_account,
    serialize_friendship_request,
    serialize_pair,
    serialize_notification,
    serialize_social_message,
)
from social.profiles import build_friend_card, build_friend_profile


def _validation_detail(exc: ValidationError) -> str:
    return str(exc.message if hasattr(exc, "message") else exc)


class SocialSearchView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_search"

    def get(self, request: Request) -> Response:
        if set(request.query_params) != {"alias"} or len(request.query_params.getlist("alias")) != 1:
            return Response({"detail": "Invalid exact alias."}, status=400)
        serializer = ExactAliasSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response({"detail": "Invalid exact alias."}, status=400)
        users = services.search_exact_alias(viewer=request.user, **serializer.validated_data)
        return Response(
            {
                "results": [
                    serialize_account(user, relationship=services.relationship_status(viewer=request.user, target=user))
                    for user in users
                ]
            }
        )


class FriendshipRequestCollectionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"

    def get(self, request: Request) -> Response:
        received, sent = services.pending_requests_for(user=request.user)
        return Response(
            {
                "received": [serialize_friendship_request(item) for item in received],
                "sent": [serialize_friendship_request(item) for item in sent],
            }
        )

    def post(self, request: Request) -> Response:
        serializer = SocialAliasRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid social request.", "errors": serializer.errors}, status=400)
        try:
            friendship_request = services.request_friendship(
                sender=request.user, **serializer.validated_data
            )
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        except services.SocialConflict as exc:
            return Response({"detail": str(exc)}, status=409)
        except ValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=400)
        friendship_request = type(friendship_request).objects.select_related("sender", "receiver").get(
            pk=friendship_request.pk
        )
        return Response({"request": serialize_friendship_request(friendship_request)}, status=201)


class FriendshipRequestActionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"
    action_name: str | None = None

    def post(self, request: Request, request_id: str, action: str | None = None) -> Response:
        resolved_action = self.action_name or action
        try:
            if resolved_action == "accept":
                pair = services.accept_friendship_request(receiver=request.user, request_id=request_id)
                return Response({"relationship": "friend", "alias": serialize_pair(pair, viewer=request.user)["alias"]})
            if resolved_action == "reject":
                services.reject_friendship_request(receiver=request.user, request_id=request_id)
                return Response({"relationship": "none"})
            if resolved_action == "cancel":
                services.cancel_friendship_request(sender=request.user, request_id=request_id)
                return Response({"relationship": "none"})
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        return Response({"detail": "Unknown social action."}, status=400)


class AcceptFriendshipRequestView(FriendshipRequestActionView):
    action_name = "accept"


class RejectFriendshipRequestView(FriendshipRequestActionView):
    action_name = "reject"


class FriendshipCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"friends": [serialize_pair(pair, viewer=request.user) for pair in services.friendships_for(user=request.user)]})


class FriendshipActionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"
    action_name: str | None = None

    def post(self, request: Request, alias: str, action: str | None = None) -> Response:
        resolved_action = self.action_name or action
        try:
            if resolved_action == "remove":
                services.remove_friendship(actor=request.user, alias=alias)
                return Response({"relationship": "none"})
            if resolved_action == "block":
                services.block_user(actor=request.user, alias=alias)
                return Response({"relationship": "blocked"})
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        except ValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=400)
        return Response({"detail": "Unknown social action."}, status=400)


class RemoveFriendshipView(FriendshipActionView):
    action_name = "remove"


class BlockUserView(FriendshipActionView):
    action_name = "block"


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"

    def post(self, request: Request, alias: str) -> Response:
        try:
            services.unblock_user(actor=request.user, alias=alias)
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        except ValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=400)
        return Response({"relationship": "none"})


class RelationshipView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, alias: str) -> Response:
        try:
            target = services._resolve_active_user(alias)
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        status = services.relationship_status(viewer=request.user, target=target)
        if status == "blocked":
            return Response({"detail": "Not found."}, status=404)
        return Response({"relationship": status, "profile": serialize_account(target, relationship=status)})


class RecommendationCollectionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"

    def post(self, request: Request) -> Response:
        serializer = RecommendationInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid recommendation.", "errors": serializer.errors}, status=400)
        try:
            message = services.send_recommendation(sender=request.user, **serializer.validated_data)
        except services.RecommendationCooldown as exc:
            response = Response(
                {
                    "detail": "recommendation_cooldown",
                    "code": "recommendation_cooldown",
                    "retry_after_seconds": exc.retry_after_seconds,
                },
                status=429,
            )
            response["Retry-After"] = str(exc.retry_after_seconds)
            return response
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        except ValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=400)
        message = type(message).objects.select_related("sender", "receiver", "work").prefetch_related(
            "work__assets"
        ).get(pk=message.pk)
        return Response({"message": serialize_social_message(message)}, status=201)


class FriendCardView(APIView):
    """GET /api/social/friends/<alias>/ -- the friends page's profile card: the
    full card for an accepted friend, or the basic one (alias, avatar, the
    relationship and the pending request) for anyone else."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, alias: str) -> Response:
        try:
            target = services._resolve_active_user(alias)
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        card = build_friend_card(viewer=request.user, target=target)
        if card is None:
            return Response({"detail": "Not found."}, status=404)
        return Response(card)


class FriendProfileView(APIView):
    """GET /api/social/friends/<alias>/profile/ -- the detailed, read-only profile
    page of an accepted friend (or of the caller), with the collection, lists
    and comments that the owner shares."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, alias: str) -> Response:
        try:
            target = services._resolve_active_user(alias)
        except services.SocialNotFound:
            return Response({"detail": "Not found."}, status=404)
        profile = build_friend_profile(viewer=request.user, target=target)
        if profile is None:
            return Response({"detail": "Not found."}, status=404)
        return Response(profile)


class NotificationCollectionView(APIView):
    """GET /api/social/notifications/ -- requests, recommendations and notices."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        items = services.notifications_for(user=request.user)
        return Response(
            {
                "notifications": [serialize_notification(item) for item in items],
                "unread": services.unread_count_for(recipient=request.user),
            }
        )


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"

    def post(self, request: Request) -> Response:
        services.mark_all_read(recipient=request.user)
        return Response({"unread": services.unread_count_for(recipient=request.user)})


class RecommendationRespondView(APIView):
    """POST /api/social/messages/<id>/respond/ -- add the recommended game to the
    backlog (``added``) or dismiss it (``dismissed``)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_mutation"

    def post(self, request: Request, message_id: str) -> Response:
        response_value = request.data.get("response")
        if not isinstance(response_value, str):
            return Response({"detail": "Invalid response."}, status=400)
        try:
            message = services.respond_to_recommendation(
                recipient=request.user, message_id=message_id, response=response_value
            )
        except services.SocialConflict as exc:
            return Response({"detail": str(exc)}, status=409)
        except ValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=400)
        if message is None:
            return Response({"detail": "Not found."}, status=404)
        return Response({"message": serialize_social_message(message), "response": message.response})


class SocialMessageCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"messages": [
            serialize_social_message(message) for message in services.inbox_for(recipient=request.user)
        ]})


class SocialMessageUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"unread_count": services.unread_count_for(recipient=request.user)})


class SocialMessageReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, message_id: str) -> Response:
        message = services.mark_message(recipient=request.user, message_id=message_id, read=True)
        if message is None:
            return Response({"detail": "Not found."}, status=404)
        return Response({"message": serialize_social_message(message)})


class SocialMessageUnreadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, message_id: str) -> Response:
        message = services.mark_message(recipient=request.user, message_id=message_id, read=False)
        if message is None:
            return Response({"detail": "Not found."}, status=404)
        return Response({"message": serialize_social_message(message)})
