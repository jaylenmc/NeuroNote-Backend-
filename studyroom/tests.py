from rest_framework.test import APITestCase
from flashcards.models import Card, Deck
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

class StudyStatsTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(email="test@gmail.com")
        
    def setUp(self):
        self.client.force_authenticate(self.user)