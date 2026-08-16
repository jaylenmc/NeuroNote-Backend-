from django.urls import path
from . import views

urlpatterns = [
    path('google/', views.googleApi, name='google-api'),
    path('auth/', views.NeuroCreateUser.as_view(), name='neuro-create-user')
]
