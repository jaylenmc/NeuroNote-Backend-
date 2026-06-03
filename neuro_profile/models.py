from django.db import models
from django.conf import settings
from django.utils import timezone

class NeuroProfile(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    primary_key=True,
    )
    jwt_token = models.CharField(null=True)
    plan = models.CharField(max_length=255, default='Note Taker')
    token_amount = models.IntegerField(default=1000)

    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_login_date = models.DateField(default=timezone.now)