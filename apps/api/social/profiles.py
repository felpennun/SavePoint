"""The profile card shown on the friends page."""

from __future__ import annotations

from django.db.models import Count, Q

from accounts.models import FavoriteSlot, ProfileVisibility
from catalogue.serializers import _cover, _platform_summary, _release_year
from library.models import LibraryEntry
from social import services
from social.models import FriendshipRequest, FriendshipRequestStatus

FAVORITE_SLOTS = 5


def _pending_request_id(*, viewer, target, status: str) -> str | None:
    if status == "pending_received":
        sender, receiver = target, viewer
    elif status == "pending_sent":
        sender, receiver = viewer, target
    else:
        return None
    request = FriendshipRequest.objects.filter(
        sender=sender, receiver=receiver, status=FriendshipRequestStatus.PENDING
    ).first()
    return str(request.id) if request is not None else None


def build_friend_card(*, viewer, target) -> dict | None:  # noqa: ANN001
    """Return the card ``viewer`` may see for ``target``.

    Anyone but an accepted friend (or the user themself) gets the basic card:
    alias, relationship and, when a request is pending, its id. Name, bio,
    photo, favorites and collection summary are friend-only, and the last two
    also honour the owner's own privacy switches.
    """
    status = services.relationship_status(viewer=viewer, target=target)
    if status == "blocked":
        return None
    card: dict = {"alias": str(target.username), "relationship": status}
    request_id = _pending_request_id(viewer=viewer, target=target, status=status)
    if request_id is not None:
        card["request_id"] = request_id
    if status not in {"friend", "self"}:
        return card

    profile = getattr(target, "profile", None)
    favorites_visible = profile is None or profile.favorites_visibility == ProfileVisibility.PUBLIC
    collection_visible = profile is None or profile.collection_visibility == ProfileVisibility.PUBLIC
    version = int(profile.updated_at.timestamp()) if profile is not None else 0

    card.update(
        {
            "display_name": str(profile.display_name) if profile is not None else "",
            "bio": str(profile.bio) if profile is not None else "",
            "avatar_url": str(profile.avatar_url) if profile is not None else "",
            "avatar_preset": profile.avatar_preset if profile is not None else None,
            "avatar_image_url": (
                f"/api/accounts/profiles/{target.username}/avatar/?v={version}"
                if profile is not None and profile.avatar_image
                else ""
            ),
            "favorites_visible": favorites_visible,
            "collection_visible": collection_visible,
        }
    )

    favorites: list[dict | None] = [None] * FAVORITE_SLOTS
    if favorites_visible:
        slots = (
            FavoriteSlot.objects.filter(user=target)
            .select_related("work")
            .prefetch_related("work__assets", "work__releases__platform")
        )
        for slot in slots:
            if 1 <= slot.slot <= FAVORITE_SLOTS:
                work = slot.work
                favorites[slot.slot - 1] = {
                    "work_id": str(work.id),
                    "work_slug": str(work.canonical_slug),
                    "title": str(work.title_en or work.original_title),
                    "year": _release_year(work),
                    "platform_summary": _platform_summary(work),
                    "cover": _cover(work),
                }
    card["favorites"] = favorites

    if collection_visible:
        counts = LibraryEntry.objects.filter(user=target).aggregate(
            games=Count("id"),
            completed=Count("id", filter=Q(current_status="completed")),
            playing=Count("id", filter=Q(current_status="playing")),
            pending=Count("id", filter=Q(current_status="pending")),
            abandoned=Count("id", filter=Q(current_status="abandoned")),
        )
        card["summary"] = counts
        card["owned_work_ids"] = [
            str(work_id)
            for work_id in LibraryEntry.objects.filter(user=target).values_list("work_id", flat=True)
        ]
    else:
        card["summary"] = None
        card["owned_work_ids"] = None
    return card


def build_friend_profile(*, viewer, target) -> dict | None:  # noqa: ANN001
    """The detailed, read-only profile of ``target`` for ``viewer``.

    Only an accepted friend (or the user themself) gets more than the basic
    card. What the owner keeps private stays out of the response: the
    collection and the favorites follow their own switches, each list its own
    visibility and each comment its own, so the page can say "not available"
    instead of showing nothing.
    """
    from catalogue.ratings import display_rating, savepoint_rating_stats
    from catalogue.serializers import _display_title
    from library.models import ContentVisibility, CustomList, GameComment
    from library.serializers import serialize_friend_collection_item

    card = build_friend_card(viewer=viewer, target=target)
    if card is None or card["relationship"] not in {"friend", "self"}:
        return card
    is_owner = card["relationship"] == "self"
    profile = getattr(target, "profile", None)
    version = int(profile.updated_at.timestamp()) if profile is not None else 0
    card["cover_image_url"] = (
        f"/api/accounts/profiles/{target.username}/cover/?v={version}"
        if profile is not None and profile.cover_image
        else ""
    )
    card["member_since"] = target.date_joined.isoformat()

    collection: list[dict] = []
    if card["collection_visible"]:
        entries = (
            LibraryEntry.objects.filter(user=target)
            .select_related("work")
            .prefetch_related("work__source_records", "work__assets", "work__releases__platform")
            .order_by("work__original_title", "id")
        )
        entries = list(entries)
        display_stats = savepoint_rating_stats(entry.work_id for entry in entries)
        # The platinum mark and the last change are shown to friends too, so the
        # collection tab can filter and sort like the owner's own collection.
        collection = [
            {
                **serialize_friend_collection_item(entry),
                "is_platinum": entry.is_platinum,
                "updated_at": entry.updated_at.isoformat(),
                # The product score (IGDB blended) shown on every card.
                "display_rating": display_rating(
                    entry.work, savepoint_stats=display_stats.get(entry.work_id, (None, 0))
                ),
            }
            for entry in entries
        ]
    card["collection"] = collection

    lists_query = CustomList.objects.filter(user=target).prefetch_related("items__work__assets")
    if not is_owner:
        lists_query = lists_query.filter(visibility=ContentVisibility.PUBLIC)
    lists = []
    for custom_list in lists_query.order_by("created_at", "id"):
        items = list(custom_list.items.order_by("position", "id"))
        lists.append(
            {
                "name": str(custom_list.name),
                "slug": str(custom_list.public_slug),
                "visibility": custom_list.visibility if is_owner else None,
                "count": len(items),
                "items": [
                    {
                        "work_slug": str(item.work.canonical_slug),
                        "title": _display_title(item.work),
                        "cover": _cover(item.work),
                    }
                    for item in items[:12]
                ],
            }
        )
    card["lists"] = lists

    comments_query = GameComment.objects.filter(user=target).select_related("work").prefetch_related("work__assets")
    if not is_owner:
        comments_query = comments_query.filter(visibility=ContentVisibility.PUBLIC)
    card["comments"] = [
        {
            "work_slug": str(comment.work.canonical_slug),
            "title": _display_title(comment.work),
            "cover": _cover(comment.work),
            "text": str(comment.text),
            "date": comment.created_at.isoformat(),
        }
        for comment in comments_query.order_by("-created_at", "id")
    ]
    return card
