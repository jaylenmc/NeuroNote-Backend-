from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models 
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class CustomManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email.split('@')[0])
        
        return super().create_user(email=email,
                                   password=password,
                                   **extra_fields
                                   )

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255)
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = CustomManager()