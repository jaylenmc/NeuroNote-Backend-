from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from .models import Card, Deck, ReviewLog
from django.utils import timezone
from django.urls import reverse
from freezegun import freeze_time
from django.contrib.auth import get_user_model


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
            msg=f"""========================== Test Cards Post (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
            )
        self.assertTrue(
            all([ele in {"question", "answer", "card_deck", "bucket", "last_review_date"} for ele in response.data]),
            msg=f"""========================== Test Cards Post (TC: Perfect Request) ==========================\n
            Key in response doesn't match expected keys: {response.data}"""
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
            msg=f"""========================== Test Cards Post (TC: Wrong Deck ID) ==========================\n
            Status Code Error: {wid_response.data}"""
            )

    def test_cards_get(self):
        # --- Perfect Request ---
        url = reverse("get-cards", args=[self.deck[0].id])

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== Test Cards Get (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertTrue(
            all([set(ele.keys()) == {"answer", "question", "card_deck", "bucket", "last_review_date"} for ele in response.data]),
            msg=f"""========================== Test Cards Get (TC: Perfect Request) ==========================\n
            Keys dont match expected response keys: {response.data}"""
        )
    
    def test_cards_get_all(self):
        # --- Perfect Request ---
        url = reverse("get-post-cards")

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== Test Cards Get (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertTrue(
            all([set(ele.keys()) == {"answer", "question", "card_deck", "bucket", "last_review_date"} for ele in response.data]),
            msg=f"""========================== Test Cards Get (TC: Perfect Request) ==========================\n
            Keys dont match expected response keys: {response.data}"""
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
            msg=f"""======================= Test Card Put (TC: Perfect Request) =======================\n
            Values didn't update: {response.data}"""
        )

    # For delete single cards and in bulk
    def test_delete_cards(self):
        print("==================== Delete Cards ====================")
        # url = reverse('delete-cards', args=[self.deck[0].pk, self.cards[2].pk])
        # response = self.client.delete(url)

        # cards = Card.objects.filter(card_deck=self.deck[0].pk).values_list('id', flat=True)
        # self.assertEqual(response.status_code, status.HTTP_200_OK, f'Status code error: {response.data}')
        # self.assertNotIn(self.cards[2].pk, list(cards), f'Error: {response.data}')
        # print(response.data)

        url = reverse('delete-cards', args=[self.deck[0].pk, self.cards[2].pk])
        url_query = f'{url}?bulk_delete=2, 3, no'
        response = self.client.delete(url_query, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, f'Status code error: {response.data}')
        ids = Card.objects.filter(card_deck__user=self.user).values_list('id', flat=True)
        self.assertNotIn(self.cards[2].pk, list(ids), f'Found in error: {response.data}')
        print(response.data)

    def test_due_cards(self):
        print("==================== Due Cards ====================")
        url = reverse('due-cards')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f'response data: {response.data}')

    def test_review_card_times(self):
        print("==================== Review Card Times ====================")
        card = Card.objects.get(id=self.cards.pop().pk)
        print(f'Before update: {card.scheduled_date}')

        with freeze_time("2025-07-07 20:40:51+00:00"):
            card.update_sm21(rating=1)
            print('--------------------------------')
            print(f'After update 1: {card.scheduled_date}')
            print(f'Stability: {card.stability}')

        with freeze_time("2025-07-09 20:41:00+00:00"):
            card.refresh_from_db()
            card.update_sm21(rating=1)
            print('--------------------------------')
            print(f'After update 2: {card.scheduled_date}')
            print(f'Stability: {card.stability}')

        with freeze_time("2025-07-10 20:41:00+00:00"):
            card.refresh_from_db()
            card.update_sm21(rating=1)
            print('--------------------------------')
            print(f'After update 2: {card.scheduled_date}')
            print(f'Stability: {card.stability}')
   
    def test_review_cards(self):
        print('====================== Review Cards ======================')
        url = reverse('review-card')
        review_session = {
            'session_time': "00:13:20",
            'review': [{
                'card_id': card.pk,
                'deck_id': card.card_deck.pk,
                'quality': 5
            } for card in self.cards]
        }
        response = self.client.put(url, review_session, format='json')
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            f'Status code error: {response.data}'
            )
        self.assertTrue(
            get_user_model().objects.get(email=self.user.email).xp > 0,
            msg=f"User xp didn't increase: {response.data}"
        )
        
        cardss = Card.objects.get(id=self.cards[-1].pk)
        cardss.last_review_date = timezone.now().isoformat()
        self.assertTrue(
            all([card.last_review_date != Card.objects.get(id=card.pk).last_review_date for card in self.cards]),
            msg=f"Cards didn't successfully update: {response.data}"
        )

        reviewed_cards = ReviewLog.objects.get(user=self.user).cards
        self.assertTrue(
            reviewed_cards.count() > 0,
            msg=f"Cards didn't save in review log: {response.data}"
        )

        print(response.data)

class DeckTestCase(APITestCase):
    def test_get_decks(self):
        print("==================== Get Decks ====================")
        url = reverse('delete-update-cards', args=[self.deck[0].pk])
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            msg=f'Status code error: {response.data}'
            )
        print(response.data)

    def test_update_deck(self):
        print("==================== Update Decks ====================")
        url = reverse('delete-update-cards', args=[self.deck[1].pk])
        data = {
            'title': 'Updated test title'
        }
        response = self.client.put(url, data)
        self.assertNotEqual(self.deck[1].title, response.data['title'])
        self.assertEqual(self.deck[1].subject, response.data['subject'])
        print(response.data)

class DFBLTestCase(APITestCase):
    def test_doing_feedback_review(self):
        print("------------------------------ Doing Feedback Review *PATCH* Test ----------------------------------")
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

        print("------------------------------ Doing Feedback Review *GET* Test ----------------------------------")
        url = reverse('dfbl-review-get', args=[self.cards[0].pk])
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data)