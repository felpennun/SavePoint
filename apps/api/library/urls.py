from django.urls import path

from library.views import (
    ClearLibraryConfigurationView,
    CommentDetailView,
    ExportCollectionView,
    LibraryConfigurationView,
    ListDetailView,
    ListItemDetailView,
    ListItemsView,
    ListReorderView,
    MyLibraryView,
    MyListsView,
    OwnedCopyDetailView,
    OwnedCopiesView,
    PopularityView,
    SetRatingView,
    SetStatusView,
    SharedCollectionView,
    SharedListView,
    WorkCommentsView,
)

app_name = "library"

urlpatterns = [
    path("entries/", MyLibraryView.as_view(), name="my-library"),
    path("profiles/<str:alias>/collection/", SharedCollectionView.as_view(), name="shared-collection"),
    path("profiles/<str:alias>/lists/<slug:list_slug>/", SharedListView.as_view(), name="shared-list"),
    path("export/collection.csv", ExportCollectionView.as_view(), name="export-collection-csv"),
    path("entries/<uuid:work_id>/status/", SetStatusView.as_view(), name="set-status"),
    path("entries/<uuid:work_id>/rating/", SetRatingView.as_view(), name="set-rating"),
    path("entries/<uuid:work_id>/copies/", OwnedCopiesView.as_view(), name="copies"),
    path("entries/<uuid:work_id>/configuration/", LibraryConfigurationView.as_view(), name="configuration"),
    path("entries/<uuid:work_id>/copies/<uuid:copy_id>/", OwnedCopyDetailView.as_view(), name="copy-detail"),
    path("entries/<uuid:work_id>/comments/", WorkCommentsView.as_view(), name="work-comments"),
    path("comments/<uuid:comment_id>/", CommentDetailView.as_view(), name="comment-detail"),
    path("lists/", MyListsView.as_view(), name="my-lists"),
    path("lists/<uuid:list_id>/", ListDetailView.as_view(), name="list-detail"),
    path("lists/<uuid:list_id>/items/", ListItemsView.as_view(), name="list-items"),
    path("lists/<uuid:list_id>/items/<uuid:item_id>/", ListItemDetailView.as_view(), name="list-item-detail"),
    path("lists/<uuid:list_id>/reorder/", ListReorderView.as_view(), name="list-reorder"),
    path("entries/<uuid:work_id>/", ClearLibraryConfigurationView.as_view(), name="clear-entry"),
    path("popularity/", PopularityView.as_view(), name="popularity"),
]
