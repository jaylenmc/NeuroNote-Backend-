from django.urls import path
from .views import FolderView

urlpatterns = [
   path('user/', FolderView.as_view(), name="folder-get-post"),
   path('user/<int:folder_id>/', FolderView.as_view(), name="folder-get-post"),
   path('user/<int:id>/', FolderView.as_view(), name="folder-del")
]