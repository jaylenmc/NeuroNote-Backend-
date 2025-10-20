from django.db import models
from authentication.models import AuthUser

class DFBLUserInteraction(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    question = models.TextField()
    studymethod = models.TextField(default='dfbl')
    attempts = models.IntegerField()
    correct_answer = models.TextField()
    user_answer = models.TextField()
    neuro_response = models.TextField()