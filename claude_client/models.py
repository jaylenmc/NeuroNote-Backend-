from django.db import models
from authentication.models import AuthUser

class DFBLUserInteraction(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    question = models.TextField()
    attempts = models.IntegerField()
    correct_answer = models.TextField()
    user_answer = models.TextField()
    neuro_response = models.TextField()

class UPSUserInteraction(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    principles = models.JSONField(default=list)
    solution_summary = models.TextField()
    explanation = models.TextField()
    neuro_response = models.TextField()
    question = models.TextField()