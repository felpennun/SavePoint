"""Library status endpoint (LIB-01, D-09/D-14): owner-scoped, transactional
state changes with append-only history. Never confirms a change to the
client before the PostgreSQL commit actually lands."""

from __future__ import annotations

from datetime import datetime, timezone

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogue.models import GameWork
from library.models import BacklogStatus, LibraryEntry, StatusTransition

VALID_STATUSES = {choice.value for choice in BacklogStatus}


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
