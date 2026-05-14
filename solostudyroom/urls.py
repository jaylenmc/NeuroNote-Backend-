from django.urls import path
from . import views

urlpatterns = [
    path("pinned/", views.PinnedResourceClass.as_view(), name="pinned-resources"),
    path("delete/<int:obj_id>/", views.PinnedResourceClass.as_view(), name="delete-resource"),
    path("create/", views.PinnedResourceClass.as_view(), name="create-pinned-resource"),
    path('study-stats/', views.studyroom_stats, name='study-stats'),

    path('avg-cards-studied-weekly/', views.avg_cards_studied_weekly, name='avg-cards-studied-weekly'),
]