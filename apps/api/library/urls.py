from django.urls import path

from library.views import (
    ClearLibraryConfigurationView,
    LibraryConfigurationView,
    MyLibraryView,
    OwnedCopyDetailView,
    OwnedCopiesView,
    PopularityView,
    SetRatingView,
    SetStatusView,
)

app_name = "library"

urlpatterns = [
    path("entries/", MyLibraryView.as_view(), name="my-library"),
    path("entries/<uuid:work_id>/status/", SetStatusView.as_view(), name="set-status"),
    path("entries/<uuid:work_id>/rating/", SetRatingView.as_view(), name="set-rating"),
    path("entries/<uuid:work_id>/copies/", OwnedCopiesView.as_view(), name="copies"),
    path("entries/<uuid:work_id>/configuration/", LibraryConfigurationView.as_view(), name="configuration"),
    path("entries/<uuid:work_id>/copies/<uuid:copy_id>/", OwnedCopyDetailView.as_view(), name="copy-detail"),
    path("entries/<uuid:work_id>/", ClearLibraryConfigurationView.as_view(), name="clear-entry"),
    path("popularity/", PopularityView.as_view(), name="popularity"),
]
