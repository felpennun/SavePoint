"""Public profile projection (PROF-02, INV-05).

This is a deliberately hand-built allowlist, never DRF's ModelSerializer
auto-introspection -- a future private field added to User/LibraryEntry/
OwnedCopy must never leak here just because it exists on the model. Only
alias, public backlog status, and aggregate counts are ever included.
Never: email, internal IDs, session data, ratings, purchase/format/
location/private-note fields, or any OwnedCopy detail.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model

from library.models import BacklogStatus, LibraryEntry

User = get_user_model()

_STATUS_ORDER = [choice.value for choice in BacklogStatus]


def _escape_text(value: str) -> str:
    """Alias/title text is returned as plain text, never markup -- the
    client renders it, it never becomes HTML/URLs here (XSS boundary)."""
    return str(value)


def build_public_profile(user) -> dict:  # noqa: ANN001
    entries = (
        LibraryEntry.objects.filter(user=user, current_status__isnull=False)
        .select_related("work")
        .order_by("work__original_title", "id")
    )

    activity = [
        {
            "work_slug": _escape_text(entry.work.canonical_slug),
            "work_title": _escape_text(entry.work.title_en or entry.work.original_title),
            "status": entry.current_status,
        }
        for entry in entries
    ]

    summary = {status: 0 for status in _STATUS_ORDER}
    for entry in entries:
        summary[entry.current_status] += 1

    # Explicit allowlist -- every key here is intentional. Do not replace
    # this dict construction with a model/serializer that could pull in
    # unreviewed fields by accident.
    return {
        "alias": _escape_text(user.username),
        "activity": activity,
        "summary": summary,
    }
