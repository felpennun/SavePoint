from django.urls import path

from library.views import OwnedCopiesView, SetRatingView, SetStatusView

app_name = "library"

urlpatterns = [
    path("entries/<uuid:work_id>/status/", SetStatusView.as_view(), name="set-status"),
    path("entries/<uuid:work_id>/rating/", SetRatingView.as_view(), name="set-rating"),
    path("entries/<uuid:work_id>/copies/", OwnedCopiesView.as_view(), name="copies"),
]
