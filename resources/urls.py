from django.urls import path
from resources import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('create/', views.ImportResource.as_view(), name='create-resource'),
    path('link/<int:id>/', views.ImportResource.as_view(), name='get-link'),
    path('delete/<int:id>/', views.ImportResource.as_view(), name='delete-resource'),
    # Presigned URLs for S3
    path("files/", views.PresignedUrls.as_view(), name="presigned-urls"),
    path("files/<str:bucket_name>/<str:object_name>/<str:region_name>/", views.PresignedUrls.as_view(), name="presigned-urls"),
]