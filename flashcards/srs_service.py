import random
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Card, ReviewGroup, ReviewGroupCard
from .srs_constants import (
    BLACKLIST_DURATION,
    BUCKET_WEIGHTS,
    HIGH_BUCKET_MEMBERSHIP_TTL,
    HIGH_MEMBERSHIP_BUCKETS,
    LOW_BUCKET_MEMBERSHIP_TTL,
    LOW_MEMBERSHIP_BUCKETS,
    STUDY_QUEUE_BLACKLIST_WINDOW,
    STUDY_QUEUE_GROUP_SIZE,
)

def get_active_study_queue(user):
    return ReviewGroup.objects.filter(
        user=user,
        group_type=ReviewGroup.GroupType.STUDY_QUEUE,
        status=ReviewGroup.Status.ACTIVE,
    ).first()

def sync_card_review_group_flags(user):
    """Set Card.is_blacklisted from active Study Queue membership."""
    group = get_active_study_queue(user)
    in_group = set()
    if group:
        in_group = set(group.memberships.values_list("card_id", flat=True))
    user_cards = Card.objects.filter(card_deck__user=user)
    user_cards.filter(is_blacklisted=True).exclude(id__in=in_group).update(
        is_blacklisted=False
    )
    if in_group:
        user_cards.filter(id__in=in_group, is_blacklisted=False).update(
            is_blacklisted=True
        )


def _blacklist_duration_for_bucket(bucket):
    if bucket in LOW_MEMBERSHIP_BUCKETS:
        return None
    if bucket in HIGH_MEMBERSHIP_BUCKETS:
        return BLACKLIST_DURATION
    return None


def _is_membership_blacklisted(membership, group, at=None):
    at = at or timezone.now()
    if at - group.created_at >= STUDY_QUEUE_BLACKLIST_WINDOW:
        return False
    card = membership.card
    duration = _blacklist_duration_for_bucket(card.bucket)
    if not duration:
        return False
    if not card.last_reviewed_at:
        return False
    # time_in_group is reset on blacklist apply; unreviewed queue cards keep join time.
    if membership.time_in_group < card.last_reviewed_at:
        return False
    return (at - membership.time_in_group) < duration


def is_card_blacklisted(user, card_id, at=None):
    group = get_active_study_queue(user)
    if not group:
        return False
    membership = (
        group.memberships.filter(card_id=card_id).select_related("card").first()
    )
    if not membership:
        return False
    return _is_membership_blacklisted(membership, group, at)


def get_slot_label(user, card_id, at=None):
    if is_card_blacklisted(user, card_id, at):
        return "Blacklisted"
    return None


def _cards_in_scope(user, group):
    qs = Card.objects.filter(card_deck__user=user)
    if group.scope == ReviewGroup.Scope.SINGLE_DECK:
        qs = qs.filter(card_deck_id=group.deck_id)
    return qs


def _blacklisted_card_ids_in_group(group, at=None):
    at = at or timezone.now()
    ids = []
    for membership in group.memberships.select_related("card"):
        if _is_membership_blacklisted(membership, group, at):
            ids.append(membership.card_id)
    return ids


def eligible_cards(user, group):
    in_group_ids = group.memberships.values_list("card_id", flat=True)
    blacklisted_ids = _blacklisted_card_ids_in_group(group)
    return _cards_in_scope(user, group).exclude(
        id__in=in_group_ids,
    ).exclude(
        id__in=blacklisted_ids,
    )


def weighted_sample(cards_qs, k, rng=None):
    rng = rng or random
    pool = list(cards_qs)
    if k <= 0 or not pool:
        return []

    selected = []
    remaining = pool[:]
    while remaining and len(selected) < k:
        weights = []
        for card in remaining:
            weights.append(BUCKET_WEIGHTS.get(card.bucket, 0.1))
        total = sum(weights)
        if total <= 0:
            pick = rng.choice(remaining)
        else:
            pick = rng.choices(remaining, weights=weights, k=1)[0]
        selected.append(pick)
        remaining.remove(pick)
    return selected


def sync_group_memberships(group):
    now = timezone.now()
    to_remove = []
    for membership in group.memberships.select_related("card"):
        age = now - membership.time_in_group
        bucket = membership.card.bucket
        if bucket in HIGH_MEMBERSHIP_BUCKETS and age >= HIGH_BUCKET_MEMBERSHIP_TTL:
            to_remove.append(membership.id)
        elif bucket in LOW_MEMBERSHIP_BUCKETS and age >= LOW_BUCKET_MEMBERSHIP_TTL:
            to_remove.append(membership.id)
    if to_remove:
        removed_card_ids = list(
            ReviewGroupCard.objects.filter(id__in=to_remove).values_list(
                "card_id", flat=True
            )
        )
        ReviewGroupCard.objects.filter(id__in=to_remove).delete()
        if removed_card_ids:
            Card.objects.filter(id__in=removed_card_ids).update(is_blacklisted=False)
    return len(to_remove)

def _add_cards_to_group(group, cards, source):
    rows = [
        ReviewGroupCard(
            group=group,
            card=card,
            source=source,
        )
        for card in cards
    ]
    ReviewGroupCard.objects.bulk_create(rows, ignore_conflicts=True)
    if cards:
        Card.objects.filter(id__in=[c.id for c in cards]).update(is_blacklisted=True)


def refresh_study_queue(group):
    sync_group_memberships(group)
    current_count = group.memberships.count()
    slots = max(0, group.group_size - current_count)
    if slots <= 0:
        return group
    candidates = eligible_cards(group.user, group)
    picked = weighted_sample(candidates, slots)
    _add_cards_to_group(group, picked, ReviewGroupCard.Source.AUTO)
    return group


def dismiss_study_queue(group):
    card_ids = list(group.memberships.values_list("card_id", flat=True))
    group.memberships.all().delete()
    if card_ids:
        Card.objects.filter(id__in=card_ids).update(is_blacklisted=False)
    group.status = ReviewGroup.Status.CANCELLED
    group.completed_at = timezone.now()
    group.save(update_fields=["status", "completed_at"])


@transaction.atomic
def create_study_queue(
    user,
    *,
    scope,
    deck=None,
    group_size=STUDY_QUEUE_GROUP_SIZE,
    is_timed=False,
    timer_seconds=None,
):
    group = ReviewGroup.objects.create(
        user=user,
        deck=deck,
        scope=scope,
        group_type=ReviewGroup.GroupType.STUDY_QUEUE,
        status=ReviewGroup.Status.ACTIVE,
        group_size=group_size,
        is_timed=is_timed,
        timer_seconds=timer_seconds,
    )
    refresh_study_queue(group)
    return group


def apply_study_queue_blacklist(group, reviewed_ratings):
    """reviewed_ratings: list of (card_id, bucket_int 1-4)."""
    if timezone.now() - group.created_at >= STUDY_QUEUE_BLACKLIST_WINDOW:
        return
    now = timezone.now()
    for card_id, bucket in reviewed_ratings:
        if bucket < 2:
            continue
        group.memberships.filter(card_id=card_id).update(time_in_group=now)


def complete_study_queue(group):
    group.status = ReviewGroup.Status.COMPLETED
    group.completed_at = timezone.now()
    group.save(update_fields=["status", "completed_at"])


def apply_timeout_ratings(user, card_ids):
    ratings = []
    for card_id in card_ids:
        card = Card.objects.filter(id=card_id, card_deck__user=user).first()
        if card:
            card.apply_bucket_rating(user, 1)
            ratings.append((card_id, 1))
    return ratings


def bucket_counts_for_user(user):
    qs = Card.objects.filter(card_deck__user=user)
    counts = {}
    for bucket, _label in Card.CardStatusOptions.choices:
        counts[bucket] = qs.filter(bucket=bucket).count()
    return counts


def group_queue_complete(group, reviewed_card_ids):
    group_card_ids = set(group.memberships.values_list("card_id", flat=True))
    if not group_card_ids:
        return False
    return group_card_ids.issubset(set(reviewed_card_ids))
