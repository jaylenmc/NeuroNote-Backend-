from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from neuro_profile.models import NeuroProfile
from .utils import reward_xp


class Deck(models.Model):
    title = models.TextField()
    subject = models.CharField(max_length=255, default="No subject provided")
    num_of_cards = models.IntegerField(default=0)
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
    bucket = models.CharField(
        choices=CardStatusOptions.choices,
        default=CardStatusOptions.BUCKET_0,
        max_length=10,
    )
    repetitions = models.IntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    is_blacklisted = models.BooleanField(
        default=False,
        help_text="True while the card is in the user's active Study Queue review group.",
    )

    @staticmethod
    def bucket_key_for_rating(rating: int) -> str:
        if rating < 1 or rating > 4:
            raise ValidationError("Bucket rating must be between 1 and 4.")
        return f"bkt_{rating}"

    def apply_bucket_rating(self, user, bucket: int):
        bucket_key = self.bucket_key_for_rating(bucket)
        self.bucket = bucket_key
        self.repetitions += 1
        self.last_reviewed_at = timezone.now()
        self.save(update_fields=["bucket", "repetitions", "last_reviewed_at"])

        profile = NeuroProfile.objects.filter(user=user).first()
        if profile:
            reward_xp(profile, bucket)


class ReviewGroup(models.Model):
    class GroupType(models.TextChoices):
        STUDY_QUEUE = "study_queue", "Study Queue"
        TIME_CRUNCH = "time_crunch", "Time Crunch"
        EXAM = "exam", "Exam"

    class Scope(models.TextChoices):
        SINGLE_DECK = "single_deck", "Single deck"
        ALL_CARDS = "all_cards", "All cards"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_groups",
    )
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, null=True, blank=True)
    scope = models.CharField(max_length=20, choices=Scope.choices)
    group_type = models.CharField(
        max_length=20,
        choices=GroupType.choices,
        default=GroupType.STUDY_QUEUE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    scheduled_study_date = models.DateField(null=True, blank=True)
    sequence_index = models.IntegerField(null=True, blank=True)
    group_size = models.IntegerField(default=20)
    is_timed = models.BooleanField(default=False)
    timer_seconds = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="active", group_type="study_queue"),
                name="unique_active_study_queue_per_user",
            ),
        ]


class ReviewGroupCard(models.Model):
    class Source(models.TextChoices):
        AUTO = "auto", "Auto"
        MANUAL = "manual", "Manual"

    group = models.ForeignKey(
        ReviewGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="group_memberships")
    time_in_group = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.AUTO)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "card"], name="unique_card_per_review_group"),
        ]


class ReviewLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_review_log",
    )
    cards = models.ManyToManyField(Card, related_name="reviewed_cards")
    session_time = models.DurationField()
    reviewed_at = models.DateTimeField(auto_now_add=True)
    review_group = models.ForeignKey(
        ReviewGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_logs",
    )


class DoingFeedbackReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    layer_one_attempts = models.IntegerField(default=0)
    layer_two_attempts = models.IntegerField(default=0)
    layer_three_attempts = models.IntegerField(default=0)
    dfbl_attempt_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
