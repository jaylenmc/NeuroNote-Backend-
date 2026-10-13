from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from .models import Card, Deck, ReviewLog
from django.urls import reverse


class CardTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(email='bob@gmail.com')
        cls.deck = Deck.objects.bulk_create([
            Deck(
                user=cls.user,
                title='Test Deck',
                subject='Test Subject'
            ),
            Deck(
                user=cls.user,
                title='Test Deck2',
                subject='Test Subject2'
            )
        ])

        cls.cards = Card.objects.bulk_create([
            Card(
                question='How many days are in a week',
                answer='7',
                card_deck=cls.deck[1],
                bucket="bkt_1"
            ),
            Card(
                question='What is cultural studies?',
                answer='The study of everyday life',
                card_deck=cls.deck[1],
                bucket="bkt_1"
            ),
            Card(
                question='How many people are in the world?',
                answer='Billions',
                card_deck=cls.deck[1],
                bucket="bkt_1"
            ),
            Card(
                question='How do you make pizza?',
                answer='With dough and sauce',
                card_deck=cls.deck[1],
                bucket="bkt_1"
            ),
            Card(
                question='How do you makasdse pizsadsandkaza?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_1"
            ),
            Card(
                question='How do you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_1"
            ),
            Card(
                question='Howwewew do you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_0"
            ),
            Card(
                question='How wefiewbfiw you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_0"
            ),
            Card(
                question='ewrknerlw do you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_0"
            ),
            Card(
                question='How do ewfeownfewo masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_0"
            ),
            Card(
                question='How do you masdsadadaake ewfnewofnoew?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                bucket="bkt_0"
            ),
        ])

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_card_post(self):
        # Perfect Request
        url = reverse('get-post-cards')
        data = {
            'question': 'how many days are in a week',
            'answer': '7',
            'card_deck': Deck.objects.first().pk
        }

        response = self.client.post(url, data, format='json')        
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertTrue(
            all([ele in {"id", "question", "answer", "card_deck", "bucket", "last_review_date", "last_reviewed_at"} for ele in response.data]),
            msg=f"Key in response doesn't match expected keys: {response.data}",
        )

        # --- Wrong Deck ID ---
        wid_data = {
            'question': 'how many days are in a week',
            'answer': '7',
            'card_deck': 100
        }
        wid_response = self.client.post(url, wid_data, format='json')
        self.assertEqual(
            wid_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Status code error: {wid_response.data}",
        )

    def test_cards_get(self):
        # --- Perfect Request ---
        url = reverse("get-cards", args=[self.deck[0].id])

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertTrue(
            all([{"answer", "question", "card_deck", "bucket", "last_review_date", "id", "last_reviewed_at"}.issubset(set(ele.keys())) for ele in response.data]),
            msg=f"Keys don't match expected response keys: {response.data}",
        )

    def test_cards_get_all(self):
        # --- Perfect Request ---
        url = reverse("get-post-cards")

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertTrue(
            all([{"answer", "question", "card_deck", "bucket", "last_review_date", "id", "last_reviewed_at"}.issubset(set(ele.keys())) for ele in response.data]),
            msg=f"Keys don't match expected response keys: {response.data}",
        )

    def test_card_put(self):
        selected_card = self.deck[0].card_deck.all().first()
        print(selected_card.__dict__.values())
        url = reverse("put-card", args=[self.deck[0].id, selected_card.id])

        data = {
            "question": "This is an updated question",
            "answer": "This is an updated answer",
            "bucket": "bucket 2"
        }
        response = self.client.put(url, data=data, format='json')
        self.assertTrue(
            response.status_code,
            status.HTTP_200_OK
        )
        card_values = self.deck[0].card_deck.all().filter(id=1).values_list("question", "answer", "bucket")
        new_vals = ["This is an updated question", "This is an updated answer", "bucket 2"]
        self.assertFalse(
            all([new_vals[idx] in set(card_values) for idx in range(3)]),
            msg=f"Values didn't update: {response.data}",
        )

    # For delete single cards and in bulk
    def test_delete_cards(self):
        url = reverse('modify-cards', args=[self.deck[0].pk, self.cards[2].pk])
        url_query = f'{url}?bulk_delete=2, 3, no'
        response = self.client.delete(url_query, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, f'Status code error: {response.data}')
        ids = Card.objects.filter(card_deck__user=self.user).values_list('id', flat=True)
        self.assertNotIn(self.cards[2].pk, list(ids), f'Found in error: {response.data}')
        print(response.data)

    def test_due_cards(self):
        url = reverse('due-cards')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f'response data: {response.data}')

    def test_review_cards(self):
        from neuro_profile.models import NeuroProfile

        NeuroProfile.objects.get_or_create(user=self.user)
        url = reverse('review-card')
        review_session = {
            'session_time': "00:13:20",
            'review': [{
                'card_id': card.pk,
                'deck_id': card.card_deck.pk,
                'bucket': 4,
            } for card in self.cards]
        }
        response = self.client.put(url, review_session, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, f'Status code error: {response.data}')

        profile = NeuroProfile.objects.get(user=self.user)
        self.assertTrue(profile.xp > 0, msg=f"User xp didn't increase: {response.data}")

        self.assertTrue(
            all(Card.objects.get(id=card.pk).last_reviewed_at is not None for card in self.cards),
            msg=f"Cards didn't successfully update: {response.data}",
        )

        reviewed_cards = ReviewLog.objects.get(user=self.user).cards
        self.assertTrue(reviewed_cards.count() > 0, msg=f"Cards didn't save in review log: {response.data}")

class DeckTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(email='bob@gmail.com')

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_specific_deck_success(self):
        deck = Deck.objects.create(
            user=self.user,
            title='Test Deck',
            subject='Test Subject',
        )

        url = reverse('get-specific-deck', args=[deck.pk])
        response = self.client.get(url, format='json')

        expected_keys = {'title', 'subject', 'num_of_cards', 'id'}
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertEqual(
            set(response.data.keys()),
            expected_keys,
            msg=f"Keys don't match expected response keys: {response.data}",
        )
        self.assertEqual(response.data['id'], deck.pk)
        self.assertEqual(response.data['title'], deck.title)
        self.assertEqual(response.data['subject'], deck.subject)

    def test_get_specific_deck_not_found(self):
        missing_id = max(Deck.objects.values_list('id', flat=True), default=0) + 10
        url = reverse('get-specific-deck', args=[missing_id])
        response = self.client.get(url, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            msg=f"Status code error: {response.data}",
        )
        self.assertEqual(
            response.data,
            {"Message": "Deck doesn't exists"},
            msg=f"Response body error: {response.data}",
        )

    def test_get_all_decks_success(self):
        deck_count = 10
        self.decks = Deck.objects.bulk_create([
            Deck(user=self.user, title=f'Deck {i}', subject=f'Subject {i}')
            for i in range(deck_count)
        ])

        url = reverse('get-post-decks')
        response = self.client.get(url, format='json')

        expected_keys = {'title', 'subject', 'num_of_cards', 'id'}
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertEqual(
            len(response.data),
            deck_count,
            msg=f"Expected {deck_count} decks: {response.data}",
        )
        for item in response.data:
            self.assertEqual(
                set(item.keys()),
                expected_keys,
                msg=f"Keys don't match expected response keys: {item}",
            )
        self_decks = [(deck.id, deck.num_of_cards) for deck in self.decks]
        self.assertTrue(
            all(deck for deck in response.data if (deck["id"], deck["num_of_cards"]) in self_decks),
            msg=f"Num of cards don't match expected response: {response.data}",
        )

    def test_get_all_decks_no_decks_404(self):
        url = reverse('get-post-decks')
        response = self.client.get(url, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            msg=f"Status code error: {response.data}",
        )
        self.assertEqual(
            response.data,
            {"Error": "User doesn't have decks"},
            msg=f"Response body error: {response.data}",
        )

    def test_deck_post_success(self):
        url = reverse('get-post-decks')
        data = {
            'title': 'New Deck',
            'subject': 'Math',
        }
        response = self.client.post(url, data, format='json')

        expected_keys = {'title', 'subject', 'num_of_cards', 'id'}
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertEqual(
            set(response.data.keys()),
            expected_keys,
            msg=f"Keys don't match expected response keys: {response.data}",
        )
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['subject'], data['subject'])
        self.assertEqual(response.data['num_of_cards'], 0)
        self.assertTrue(
            Deck.objects.filter(pk=response.data['id'], user=self.user).exists(),
            msg=f"Deck was not created: {response.data}",
        )

    def test_deck_post_duplicate_title(self):
        Deck.objects.create(
            user=self.user,
            title='Existing Deck',
            subject='Science',
        )
        url = reverse('get-post-decks')
        response = self.client.post(
            url,
            {'title': 'existing deck', 'subject': 'Other'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
            msg=f"Status code error: {response.data}",
        )

class DFBLTestCase(APITestCase):
    def test_doing_feedback_review(self):
        url = reverse('dfbl-review')

        data = {
            'card': self.cards[0].pk,
            'layer_attempts': 34,
            'layer': 1
        }
        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data)

        url = reverse('dfbl-review-get', args=[self.cards[0].pk])
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data)