"""Library status endpoint (LIB-01, D-09/D-14): owner-scoped, transactional
state changes with append-only history. Never confirms a change to the
client before the PostgreSQL commit actually lands."""

from __future__ import annotations

from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from catalogue.models import GameWork
from catalogue.ratings import display_rating, savepoint_rating_stats
from catalogue.serializers import _cover, _platform_summary
from library import services
from library.export import EXPORT_FILENAME, render_collection_csv
from library.models import BacklogStatus, CustomList, CustomListItem, GameComment, LibraryEntry, OwnedCopy, StatusTransition
from library.popularity import rank_popularity_v1
from library.serializers import (
    AddListItemSerializer,
    CommentInputSerializer,
    CreateOwnedCopyRequestSerializer,
    CustomListInputSerializer,
    LibraryConfigurationSerializer,
    RatingRequestSerializer,
    ReorderListSerializer,
    serialize_comment,
    serialize_copy,
    serialize_friend_collection_item,
    serialize_friend_list,
    serialize_list,
    serialize_shared_comment,
)
from social.policies import ProfileAccess, resolve_profile_access

VALID_STATUSES = {choice.value for choice in BacklogStatus}
User = get_user_model()


def _generic_not_found() -> Response:
    return Response({"detail": "Not found."}, status=404)


def _shared_owner(request: Request, alias: str):  # noqa: ANN001
    """Resolve alias and relationship before querying protected content."""
    owner = User.objects.filter(username=alias, is_active=True).first()
    if owner is None:
        return None, ProfileAccess.HIDDEN
    access = resolve_profile_access(viewer=request.user, owner=owner)
    if access not in {ProfileAccess.OWNER, ProfileAccess.ACCEPTED_FRIEND}:
        return None, access
    return owner, access


def _service_error_detail(exc: ValidationError) -> str:
    return str(exc.message if hasattr(exc, "message") else exc)


class SharedCollectionView(APIView):
    """GET a friend's collection through the canonical alias locator."""

    permission_classes = [AllowAny]

    def get(self, request: Request, alias: str) -> Response:
        owner, access = _shared_owner(request, alias)
        if owner is None:
            return _generic_not_found()
        profile = getattr(owner, "profile", None)
        if access == ProfileAccess.ACCEPTED_FRIEND and profile is not None and profile.collection_visibility != "public":
            return _generic_not_found()
        entries = (
            LibraryEntry.objects.filter(user=owner)
            .select_related("work")
            .prefetch_related("work__assets", "work__releases__platform")
            .order_by("work__original_title", "id")
        )
        return Response({"items": [serialize_friend_collection_item(entry) for entry in entries]})


class SharedListView(APIView):
    """GET a public list through the owner alias + stable public slug."""

    permission_classes = [AllowAny]

    def get(self, request: Request, alias: str, list_slug: str) -> Response:
        owner, access = _shared_owner(request, alias)
        if owner is None:
            return _generic_not_found()
        custom_list = (
            CustomList.objects.filter(user=owner, public_slug=list_slug)
            .prefetch_related(
                "items__work__assets",
                "items__work__releases__platform",
            )
            .first()
        )
        if custom_list is None:
            return _generic_not_found()
        if access == ProfileAccess.ACCEPTED_FRIEND and custom_list.visibility != "public":
            return _generic_not_found()
        work_ids = [item.work_id for item in custom_list.items.all()]
        entries_by_work = {
            entry.work_id: entry
            for entry in LibraryEntry.objects.filter(user=owner, work_id__in=work_ids).select_related("work")
        }
        return Response(serialize_friend_list(custom_list, entries_by_work=entries_by_work))


class MyLibraryView(APIView):
    """GET /api/library/entries/ -- the caller's own collection (Collection
    page, D-13/D-14). Owner-scoped by construction: filtered to
    request.user, never accepts a target user."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        entries = (
            LibraryEntry.objects.filter(user=request.user)
            .filter(
                Q(current_status__isnull=False)
                | Q(rating_half_steps__isnull=False)
                | Q(work__owned_copies__user=request.user)
            )
            .select_related("work")
            .prefetch_related("work__source_records", "work__assets", "work__releases__platform")
            .annotate(owned_copy_count=Count("work__owned_copies", distinct=True))
            .distinct()
            .order_by("work__original_title", "id")
        )
        entries = list(entries)
        display_stats = savepoint_rating_stats(entry.work_id for entry in entries)
        items = []
        summary = {choice.value: 0 for choice in BacklogStatus}
        for entry in entries:
            if entry.current_status is not None:
                summary[entry.current_status] += 1
            items.append(
                {
                    "work_id": str(entry.work_id),
                    "work_slug": entry.work.canonical_slug,
                    "work_title": entry.work.title_en or entry.work.original_title,
                    "status": entry.current_status,
                    "rating_half_steps": entry.rating_half_steps,
                    # Product-facing blended score; deliberately separate
                    # from the owner's personal StarRating below the card.
                    "display_rating": display_rating(
                        entry.work,
                        savepoint_stats=display_stats.get(entry.work_id, (None, 0)),
                    ),
                    "owned_copy_count": entry.owned_copy_count,
                    # Owner-only mark, rendered by the client exclusively on
                    # the Collection page -- never on the shared catalogue
                    # or the public profile (this endpoint itself is already
                    # IsAuthenticated + owner-scoped, so that's enforced here
                    # too, not just by client-side omission).
                    "is_platinum": entry.is_platinum,
                    # Enough for the Collection page's client-side sorts
                    # (recently_updated / release_year) to actually work; the
                    # enrichment is kept in the same allowlisted shape as
                    # catalogue cards so the collection needs no extra API
                    # requests per item.
                    "year": entry.work.first_release_date.year if entry.work.first_release_date else None,
                    "platform_summary": _platform_summary(entry.work),
                    "cover": _cover(entry.work),
                    "updated_at": entry.updated_at.isoformat(),
                }
            )
        return Response({"items": items, "summary": summary})


class SetStatusView(APIView):
    """GET/POST /api/library/entries/<work_id>/status/

    GET returns the caller's current status for this work (None if never
    set) -- the UI reads this back after every reload rather than trusting
    client-side state, per the plan's prohibition on confirming a status
    before the PostgreSQL commit actually lands."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, work_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        entry = LibraryEntry.objects.filter(user=request.user, work=work).first()
        return Response({"status": entry.current_status if entry else None})

    def post(self, request: Request, work_id: str) -> Response:
        new_status = request.data.get("status")
        if new_status not in VALID_STATUSES:
            return Response({"detail": "Invalid status."}, status=400)

        # D-11: DLC/expansions are never independently actionable.
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)

        with transaction.atomic():
            entry, _ = LibraryEntry.objects.select_for_update().get_or_create(
                user=request.user, work=work, defaults={"current_status": None}
            )
            old_status = entry.current_status
            if old_status == new_status:
                # Idempotent retry: identical resubmission creates no
                # duplicate history entry (CAT-04/CAT-06-adjacent concurrency
                # contract, applied here to status transitions).
                return Response({"status": entry.current_status, "changed": False})

            entry.current_status = new_status
            entry.save(update_fields=["current_status", "updated_at"])
            StatusTransition.objects.create(
                entry=entry,
                from_status=old_status,
                to_status=new_status,
                changed_at=datetime.now(timezone.utc),
            )
            # Only reachable after both writes above have actually executed
            # inside this still-open transaction; Response() below is built
            # from the just-committed `entry`, not an optimistic guess.

        return Response({"status": entry.current_status, "changed": True})


class SetRatingView(APIView):
    """GET/POST /api/library/entries/<work_id>/rating/ {"rating_half_steps": 7|null}"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, work_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        entry = LibraryEntry.objects.filter(user=request.user, work=work).first()
        return Response({"rating_half_steps": entry.rating_half_steps if entry else None})

    def post(self, request: Request, work_id: str) -> Response:
        serializer = RatingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid rating.", "errors": serializer.errors}, status=400)

        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        entry = services.set_rating(
            user=request.user, work=work, rating_half_steps=serializer.validated_data["rating_half_steps"]
        )
        return Response({"rating_half_steps": entry.rating_half_steps})


class OwnedCopiesView(APIView):
    """GET/POST /api/library/entries/<work_id>/copies/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, work_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        copies = OwnedCopy.objects.filter(user=request.user, work=work)
        return Response({"copies": [serialize_copy(copy) for copy in copies]})

    def post(self, request: Request, work_id: str) -> Response:
        serializer = CreateOwnedCopyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid copy request.", "errors": serializer.errors}, status=400)

        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        data = serializer.validated_data
        try:
            copy, created = services.create_owned_copy(
                user=request.user,
                work=work,
                release_id=str(data["release_id"]),
                edition_id=str(data["edition_id"]) if data.get("edition_id") else None,
                format=data["format"],
                idempotency_key=data["idempotency_key"],
                purchase_date=data.get("purchase_date"),
                price=data.get("price"),
                currency=data.get("currency"),
                store=data.get("store"),
                conservation_state=data.get("conservation_state"),
                storage_location=data.get("storage_location"),
            )
        except ValidationError as exc:
            return Response({"detail": str(exc.message if hasattr(exc, "message") else exc)}, status=400)

        return Response({"copy": serialize_copy(copy), "created": created}, status=201 if created else 200)


class LibraryConfigurationView(APIView):
    """GET/POST the complete status/rating/platinum/copies configuration for
    one work. GET is used by the client to read back is_platinum without a
    fifth bespoke endpoint (status/rating/copies already have their own
    narrower GETs, kept as-is)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, work_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        entry = LibraryEntry.objects.filter(user=request.user, work=work).first()
        return Response(
            {
                "status": entry.current_status if entry else None,
                "rating_half_steps": entry.rating_half_steps if entry else None,
                "is_platinum": entry.is_platinum if entry else False,
                "copies": [
                    serialize_copy(copy)
                    for copy in OwnedCopy.objects.filter(user=request.user, work=work)
                ],
            }
        )

    def post(self, request: Request, work_id: str) -> Response:
        serializer = LibraryConfigurationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid library configuration.", "errors": serializer.errors}, status=400)
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        try:
            entry = services.save_library_configuration(work=work, user=request.user, **serializer.validated_data)
        except ValidationError as exc:
            return Response({"detail": str(exc.message if hasattr(exc, "message") else exc)}, status=400)
        return Response(
            {
                "status": entry.current_status if entry else None,
                "rating_half_steps": entry.rating_half_steps if entry else None,
                "is_platinum": entry.is_platinum if entry else False,
                "copies": [
                    serialize_copy(copy)
                    for copy in OwnedCopy.objects.filter(user=request.user, work=work)
                ],
            }
        )


class OwnedCopyDetailView(APIView):
    """DELETE one owner-scoped copy."""

    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, work_id: str, copy_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        if not services.delete_owned_copy(user=request.user, work=work, copy_id=copy_id):
            return Response({"detail": "Copy not found."}, status=404)
        return Response(status=204)


class ClearLibraryConfigurationView(APIView):
    """DELETE the work from the caller's collection and remove all config."""

    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, work_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        services.clear_library_configuration(user=request.user, work=work)
        return Response(status=204)


class PopularityView(APIView):
    """GET /api/library/popularity/

    Public (REC-02): the baseline is a demo-wide aggregate, not
    personalized data, so it carries no owner-scoping. Always local
    computation, never a live/external call.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "popularity"

    def get(self, request: Request) -> Response:
        return Response(rank_popularity_v1())


class ExportCollectionView(APIView):
    """GET /api/library/export/collection.csv (PORT-01/PORT-04, D-08/D-09).

    Owner-scoped by construction: ``render_collection_csv`` queries only
    ``request.user``'s own favorites/collection/copies/comments/list items.
    Returns a single deterministic, versioned, UTF-8 CSV -- there is no JSON
    variant and no import counterpart; both remain explicitly pending
    (see ``05-PORTABILITY-RECONCILIATION.md``)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> HttpResponse:
        content = render_collection_csv(request.user)
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{EXPORT_FILENAME}"'
        response["Content-Length"] = str(len(content))
        return response


class WorkCommentsView(APIView):
    """GET/POST /api/library/entries/<work_id>/comments/ (LIB-03/D-04/D-05).

    GET is public: every ``public`` comment for this work, plus the
    caller's own comment regardless of visibility when authenticated. POST
    requires authentication and creates the caller's single comment for
    this work -- a second attempt returns 409 without touching the
    existing row."""

    permission_classes = [AllowAny]

    def get_permissions(self) -> list:
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request: Request, work_id: str) -> Response:
        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        viewer = request.user if request.user.is_authenticated else None
        if viewer is None:
            return Response({"comments": []})
        comments = services.list_visible_comments(work=work, viewer=viewer)
        visible_comments = [
            comment
            for comment in comments
            if (
                resolve_profile_access(viewer=viewer, owner=comment.user) == ProfileAccess.OWNER
                or (
                    resolve_profile_access(viewer=viewer, owner=comment.user)
                    == ProfileAccess.ACCEPTED_FRIEND
                    and comment.visibility == "public"
                )
            )
        ]
        return Response({"comments": [serialize_shared_comment(comment) for comment in visible_comments]})

    def post(self, request: Request, work_id: str) -> Response:
        serializer = CommentInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid comment.", "errors": serializer.errors}, status=400)

        work = get_object_or_404(GameWork, id=work_id, is_dlc=False)
        try:
            comment = services.create_comment(user=request.user, work=work, **serializer.validated_data)
        except services.CommentAlreadyExists:
            return Response({"detail": "You already have a comment for this work."}, status=409)
        except ValidationError as exc:
            return Response({"detail": _service_error_detail(exc)}, status=400)

        return Response(serialize_comment(comment, viewer=request.user), status=201)


class CommentDetailView(APIView):
    """GET/PATCH/DELETE /api/library/comments/<comment_id>/ -- owner-only by
    construction: every query below filters on ``user=request.user``, so a
    non-owner's request is indistinguishable from a nonexistent comment."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, comment_id: str) -> Response:
        comment = GameComment.objects.filter(id=comment_id, user=request.user).select_related("user").first()
        if comment is None:
            return Response({"detail": "Not found."}, status=404)
        return Response(serialize_comment(comment, viewer=request.user))

    def patch(self, request: Request, comment_id: str) -> Response:
        serializer = CommentInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"detail": "Invalid comment.", "errors": serializer.errors}, status=400)

        comment = GameComment.objects.filter(id=comment_id, user=request.user).select_related("user").first()
        if comment is None:
            return Response({"detail": "Not found."}, status=404)
        try:
            comment = services.update_comment(comment=comment, **serializer.validated_data)
        except ValidationError as exc:
            return Response({"detail": _service_error_detail(exc)}, status=400)

        return Response(serialize_comment(comment, viewer=request.user))

    def delete(self, request: Request, comment_id: str) -> Response:
        if not services.delete_comment(user=request.user, comment_id=comment_id):
            return Response({"detail": "Not found."}, status=404)
        return Response(status=204)


class MyListsView(APIView):
    """GET/POST /api/library/lists/ -- the caller's own custom lists
    (LIB-04/D-06/D-07). Owner-scoped by construction: filtered to
    request.user, never accepts a target user."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        custom_lists = (
            CustomList.objects.filter(user=request.user)
            .prefetch_related("items__work")
            .order_by("created_at", "id")
        )
        return Response({"lists": [serialize_list(custom_list) for custom_list in custom_lists]})

    def post(self, request: Request) -> Response:
        serializer = CustomListInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid list.", "errors": serializer.errors}, status=400)
        try:
            custom_list = services.create_list(user=request.user, **serializer.validated_data)
        except ValidationError as exc:
            return Response({"detail": _service_error_detail(exc)}, status=400)
        return Response(serialize_list(custom_list), status=201)


class ListDetailView(APIView):
    """GET/PATCH/DELETE /api/library/lists/<list_id>/ -- owner-only."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, list_id: str) -> Response:
        custom_list = (
            CustomList.objects.filter(id=list_id, user=request.user).prefetch_related("items__work").first()
        )
        if custom_list is None:
            return Response({"detail": "Not found."}, status=404)
        return Response(serialize_list(custom_list))

    def patch(self, request: Request, list_id: str) -> Response:
        serializer = CustomListInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"detail": "Invalid list.", "errors": serializer.errors}, status=400)

        custom_list = CustomList.objects.filter(id=list_id, user=request.user).first()
        if custom_list is None:
            return Response({"detail": "Not found."}, status=404)
        try:
            custom_list = services.update_list(custom_list=custom_list, **serializer.validated_data)
        except ValidationError as exc:
            return Response({"detail": _service_error_detail(exc)}, status=400)
        return Response(serialize_list(custom_list))

    def delete(self, request: Request, list_id: str) -> Response:
        deleted, _ = CustomList.objects.filter(id=list_id, user=request.user).delete()
        if not deleted:
            return Response({"detail": "Not found."}, status=404)
        return Response(status=204)


class ListItemsView(APIView):
    """POST /api/library/lists/<list_id>/items/ -- append one work already
    in the caller's own collection to the caller's own list."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, list_id: str) -> Response:
        serializer = AddListItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid item.", "errors": serializer.errors}, status=400)

        custom_list = CustomList.objects.filter(id=list_id, user=request.user).first()
        if custom_list is None:
            return Response({"detail": "Not found."}, status=404)

        work = get_object_or_404(GameWork, id=str(serializer.validated_data["work_id"]), is_dlc=False)
        try:
            services.add_list_item(user=request.user, custom_list=custom_list, work=work)
        except ValidationError as exc:
            return Response({"detail": _service_error_detail(exc)}, status=400)

        custom_list = CustomList.objects.filter(id=list_id, user=request.user).prefetch_related("items__work").first()
        return Response(serialize_list(custom_list), status=201)


class ListItemDetailView(APIView):
    """DELETE /api/library/lists/<list_id>/items/<item_id>/ -- owner-only,
    filtered through the parent list's ownership in the same query."""

    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, list_id: str, item_id: str) -> Response:
        deleted, _ = CustomListItem.objects.filter(
            id=item_id, list_id=list_id, list__user=request.user
        ).delete()
        if not deleted:
            return Response({"detail": "Not found."}, status=404)
        return Response(status=204)


class ListReorderView(APIView):
    """POST /api/library/lists/<list_id>/reorder/

    Body: ``{"expected_version": N, "item_ids": [...]}``. ``expected_version``
    is mandatory -- a request without it is rejected with 400 before any
    mutation. A stale version is rejected with 409 without touching any
    item; only a matching version is processed under ``select_for_update()``
    and committed atomically (D-06, Pattern 4)."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, list_id: str) -> Response:
        serializer = ReorderListSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid reorder request.", "errors": serializer.errors}, status=400)

        if not CustomList.objects.filter(id=list_id, user=request.user).exists():
            return Response({"detail": "Not found."}, status=404)

        try:
            custom_list = services.reorder_list_items(
                user=request.user,
                list_id=list_id,
                expected_version=serializer.validated_data["expected_version"],
                item_ids=[str(item_id) for item_id in serializer.validated_data["item_ids"]],
            )
        except services.StaleListVersion:
            return Response({"detail": "List has changed; reload and try again.", "conflict": True}, status=409)
        except ValidationError as exc:
            return Response({"detail": _service_error_detail(exc)}, status=400)

        custom_list = CustomList.objects.filter(id=custom_list.id).prefetch_related("items__work").first()
        return Response(serialize_list(custom_list))
