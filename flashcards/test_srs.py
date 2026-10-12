import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase

from neuro_profile.models import NeuroProfile
from .models import Card, Deck, ReviewGroup, ReviewGroupCard
from .srs_service import is_card_blacklisted
from .srs_service import sync_group_memberships, weighted_sample


class SRSTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email="srs@test.com", password="pass")
        NeuroProfile.objects.create(user=cls.user)
        cls.deck = Deck.objects.create(user=cls.user, title="SRS Deck", subject="Bio")
        cls.cards = []
        buckets = ["bkt_0", "bkt_1", "bkt_2", "bkt_3", "bkt_4"]
        for i in range(15):
            cls.cards.append(
                Card.objects.create(
                    question=f"Q{i}",
                    answer=f"A{i}",
                    card_deck=cls.deck,
                    bucket=buckets[i % 5],
                )
            )

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        ReviewGroup.objects.filter(user=self.user).delete()

    def test_start_study_queue_single_deck(self):
        url = reverse("study-queue-start")
        response = self.client.post(url, {"deck_id": self.deck.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["scope"], "single_deck")
        self.assertTrue(len(response.data["cards"]) > 0)

    def test_only_one_active_queue(self):
        url = reverse("study-queue-start")
        self.client.post(url, {"deck_id": self.deck.id}, format="json")
        conflict = self.client.post(url, {"deck_id": self.deck.id}, format="json")
        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)

    def test_dismiss_study_queue(self):
        self.client.post(reverse("study-queue-start"), {"deck_id": self.deck.id}, format="json")
        response = self.client.delete(reverse("study-queue-current"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            ReviewGroup.objects.filter(user=self.user, status=ReviewGroup.Status.ACTIVE).count(),
            0,
        )

    def test_review_rejects_quality(self):
        card = self.cards[0]
        payload = {
            "session_time": "00:05:00",
            "review": [
                {
                    "card_id": card.id,
                    "deck_id": self.deck.id,
                    "quality": 5,
                }
            ],
        }
        response = self.client.put(reverse("review-card"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_bucket_updates_card(self):
        card = self.cards[0]
        payload = {
            "session_time": "00:05:00",
            "review": [{"card_id": card.id, "deck_id": self.deck.id, "bucket": 3}],
        }
        response = self.client.put(reverse("review-card"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.bucket, "bkt_3")
        self.assertIsNotNone(card.last_reviewed_at)

    def test_blacklist_within_24h(self):
        start = self.client.post(
            reverse("study-queue-start"),
            {"deck_id": self.deck.id, "group_size": 5},
            format="json",
        )
        group_id = start.data["id"]
        card = Card.objects.get(id=start.data["cards"][0]["id"])
        payload = {
            "session_time": "00:10:00",
            "study_group_id": group_id,
            "review": [{"card_id": card.id, "deck_id": self.deck.id, "bucket": 4}],
        }
        self.client.put(reverse("review-card"), payload, format="json")
        self.assertTrue(is_card_blacklisted(self.user, card.id))

    def test_blacklist_not_applied_for_bucket_1(self):
        start = self.client.post(
            reverse("study-queue-start"),
            {"deck_id": self.deck.id, "group_size": 5},
            format="json",
        )
        group_id = start.data["id"]
        card = Card.objects.get(id=start.data["cards"][0]["id"])
        payload = {
            "session_time": "00:10:00",
            "study_group_id": group_id,
            "review": [{"card_id": card.id, "deck_id": self.deck.id, "bucket": 1}],
        }
        self.client.put(reverse("review-card"), payload, format="json")
        self.assertFalse(is_card_blacklisted(self.user, card.id))

    def test_sync_removes_high_bucket_after_24h(self):
        group_resp = self.client.post(
            reverse("study-queue-start"),
            {"deck_id": self.deck.id, "group_size": 3},
            format="json",
        )
        group = ReviewGroup.objects.get(id=group_resp.data["id"])
        membership = group.memberships.select_related("card").first()
        card = membership.card
        card.bucket = Card.CardStatusOptions.BUCKET_3
        card.save(update_fields=["bucket"])

        with freeze_time(membership.time_in_group + timedelta(hours=25)):
            removed = sync_group_memberships(group)
        self.assertGreaterEqual(removed, 1)
        self.assertFalse(group.memberships.filter(id=membership.id).exists())

    def test_due_endpoint_with_active_queue(self):
        self.client.post(reverse("study-queue-start"), {"deck_id": self.deck.id}, format="json")
        response = self.client.get(reverse("due-cards"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("cards", response.data)
        self.assertIn("bucket_counts", response.data)
        self.assertIsNotNone(response.data["study_group_id"])

    def test_weighted_sample_deterministic(self):
        rng = random.Random(42)
        cards = list(Card.objects.filter(card_deck=self.deck))
        sample = weighted_sample(cards, 5, rng=rng)
        self.assertEqual(len(sample), 5)

    def test_manual_add_and_remove_card(self):
        self.client.post(reverse("study-queue-start"), {"deck_id": self.deck.id}, format="json")
        extra = Card.objects.create(
            question="extra",
            answer="extra",
            card_deck=self.deck,
            bucket="bkt_0",
        )
        add = self.client.post(reverse("study-queue-card-add"), {"card_id": extra.id}, format="json")
        self.assertEqual(add.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in add.data["cards"]]
        self.assertIn(extra.id, ids)

        remove = self.client.delete(reverse("study-queue-card-remove", args=[extra.id]))
        self.assertEqual(remove.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in remove.data["cards"]]
        self.assertNotIn(extra.id, ids)

    def test_mastery_uses_buckets(self):
        for card in self.cards:
            card.bucket = Card.CardStatusOptions.BUCKET_4
            card.save(update_fields=["bucket"])
        url = reverse("delete-update-cards", args=[self.deck.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mastery_progress"], 100.0)
        self.assertTrue(response.data["is_mastered"])
