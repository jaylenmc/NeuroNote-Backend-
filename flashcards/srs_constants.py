from datetime import timedelta

from .models import Card

STUDY_QUEUE_GROUP_SIZE = 20
BLACKLIST_DURATION = timedelta(hours=1)
HIGH_BUCKET_MEMBERSHIP_TTL = timedelta(hours=24)
LOW_BUCKET_MEMBERSHIP_TTL = timedelta(days=2)
STUDY_QUEUE_BLACKLIST_WINDOW = timedelta(hours=24)

MASTERED_BUCKETS = {
    Card.CardStatusOptions.BUCKET_3,
    Card.CardStatusOptions.BUCKET_4,
}

BUCKET_WEIGHTS = {
    Card.CardStatusOptions.BUCKET_0: 0.10,
    Card.CardStatusOptions.BUCKET_1: 0.35,
    Card.CardStatusOptions.BUCKET_2: 0.25,
    Card.CardStatusOptions.BUCKET_3: 0.20,
    Card.CardStatusOptions.BUCKET_4: 0.10,
}

HIGH_MEMBERSHIP_BUCKETS = {
    Card.CardStatusOptions.BUCKET_2,
    Card.CardStatusOptions.BUCKET_3,
    Card.CardStatusOptions.BUCKET_4,
}

LOW_MEMBERSHIP_BUCKETS = {
    Card.CardStatusOptions.BUCKET_0,
    Card.CardStatusOptions.BUCKET_1,
}
