from django.urls import path

from library.views import SetStatusView

app_name = "library"

urlpatterns = [
    path("entries/<uuid:work_id>/status/", SetStatusView.as_view(), name="set-status"),
]
