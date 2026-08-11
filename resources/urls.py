from django.urls import path
from resources import views

urlpatterns = [
    # PDF Resource endpoints
    path('pdf/<int:id>/', views.PDFResource.as_view(), name='pdf-get-delete'),
    # Link Resource endpoints
    path('link/', views.LinkResource.as_view(), name='link-post'),
    path('link/<int:id>', views.LinkResource.as_view(), name='link-get'),
    path('link/delete/<int:id>/', views.LinkResource.as_view(), name='link-delete'),
    # Presigned URLs for S3
    path("files/", views.PresignedUrls.as_view(), name="presigned-urls-post"),
    path("files/<str:object_name>/", views.PresignedUrls.as_view(), name="presigned-urls-get"),
    # All Resources
    path('all/', views.all_resources, name="all-resources")
]