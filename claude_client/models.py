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
    question = models.TextField()
    neuro_response = models.TextField()

    # Explanation field
    explanation = models.TextField(null=True, blank=True)
    
    # Connection fields
    principles = models.JSONField(default=list, null=True, blank=True)
    solution_summary = models.TextField(null=True, blank=True)