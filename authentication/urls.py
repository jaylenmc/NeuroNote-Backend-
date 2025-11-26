from django.urls import path
from . import views

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('options/', views.options_test, name='options-test'),
    path('google/', views.googleApi, name='google-api'),
    path('token/refresh/', views.CookieTokenRefreshView.as_view(), name='jwt-refresh'),
]
