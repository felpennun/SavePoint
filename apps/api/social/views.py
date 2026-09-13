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
    SocialAliasRequestSerializer,
    serialize_account,
    serialize_friendship_request,
    serialize_pair,
)


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
