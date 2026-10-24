from django.urls import path

from .views import FileDetailView, FileDownloadURLView, FileHistoryView, FileListCreateView

urlpatterns = [
    path("files/", FileListCreateView.as_view(), name="file_list_create"),
    path("files/<uuid:pk>/", FileDetailView.as_view(), name="file_detail"),
    path("files/<uuid:pk>/versions/", FileHistoryView.as_view(), name="file_history"),
    path("files/<uuid:pk>/download-url/", FileDownloadURLView.as_view(), name="file_download_url"),
]
