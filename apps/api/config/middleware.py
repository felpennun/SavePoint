"""Request hygiene middleware."""

from __future__ import annotations

from django.http import JsonResponse


class RejectNulBytesMiddleware:
    """Answer 400 to a request whose path or query string carries a NUL byte.

    PostgreSQL cannot store NUL characters, so such a value used to reach a
    query and surface as a 500; it is never a legitimate request.
    """

    def __init__(self, get_response):  # noqa: ANN001
        self.get_response = get_response

    def __call__(self, request):  # noqa: ANN001
        raw_query = request.META.get("QUERY_STRING", "")
        if "\x00" in request.path or "\x00" in raw_query or "%00" in raw_query.lower() or "%00" in request.path.lower():
            return JsonResponse({"detail": "Invalid request."}, status=400)
        return self.get_response(request)
