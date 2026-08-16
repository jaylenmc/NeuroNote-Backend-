from django.db import models
from .utils import reward_xp
from django.conf import settings

class Deck(models.Model):
    title = models.TextField()
    subject = models.CharField(max_length=255, default="No subject provided")
    num_of_cards = models.IntegerField(default=0)
    mastery_progress = models.FloatField(default=0)
    is_mastered = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

class Card(models.Model):
    class CardStatusOptions(models.TextChoices):
        BUCKET_0 = "bkt_0", "New Card"
        BUCKET_1 = "bkt_1", "Bucket 1"
        BUCKET_2 = "bkt_2", "Bucket 2"
        BUCKET_3 = "bkt_3", "Bucket 3"
        BUCKET_4 = "bkt_4", "Bucket 4"

    question = models.TextField()
    answer = models.TextField()
    card_deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="card_deck")
    bucket = models.CharField(choices=CardStatusOptions.choices, default=CardStatusOptions.BUCKET_0)
    repetitions = models.IntegerField(default=0)
    last_review_date = models.DateField(auto_now=True, null=True, blank=True)

class ReviewLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_review_log")
    cards = models.ManyToManyField(Card, related_name="reviewed_cards")
    session_time = models.DurationField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

class DoingFeedbackReview(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card=models.ForeignKey(Card, on_delete=models.CASCADE)
    layer_one_attempts=models.IntegerField(default=0)
    layer_two_attempts=models.IntegerField(default=0)
    layer_three_attempts=models.IntegerField(default=0)
    dfbl_attempt_date=models.DateTimeField(auto_now_add=True, null=True, blank=True)