"""Root URL configuration; feature routes are added by downstream plans."""

from django.http import JsonResponse
from django.urls import path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [path("health/", health, name="health")]

