from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models 
from django.contrib.auth import get_user_model
from rest_framework import exceptions

class CustomManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email.split('@')[0])
        user = super().create_user(email=email,
                                   password=password,
                                   **extra_fields
                                   )
        return user

    def get_or_create(self, email, password=None):
        try:
            user = self.get(email=email)
            print(user)
            return user, False
        except self.model.DoesNotExist:
            return self.create_user(email=email, password=password), True
    
class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255)
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = CustomManager()