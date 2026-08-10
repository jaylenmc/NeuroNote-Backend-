from django.urls import path
from . import views

urlpatterns = [
    path("files/", views.PresignedUrls.as_view(), name="presigned-urls"),
    path("files/<str:bucket_name>/<str:object_name>/<str:region_name>/", views.PresignedUrls.as_view(), name="presigned-urls"),
]