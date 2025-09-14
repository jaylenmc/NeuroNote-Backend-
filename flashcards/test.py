from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from .models import Card, Deck, ReviewLog
from authentication.models import AuthUser
from django.utils import timezone
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from django.urls import reverse
from freezegun import freeze_time


class CardTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create_user(email='bob@gmail.com', password='12345')
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
        time = timezone.now() - timedelta(hours=1)

        cls.cards = Card.objects.bulk_create([
            Card(
                question='How many days are in a week',
                answer='7',
                card_deck=cls.deck[1],
                scheduled_date=(timezone.now() + timedelta(hours=2)).isoformat(),
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.MASTERED
            ),
            Card(
                question='What is cultural studies?',
                answer='The study of everyday life',
                card_deck=cls.deck[1],
                scheduled_date=(timezone.now() + timedelta(hours=2)).isoformat(),
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.MASTERED
            ),
            Card(
                question='How many people are in the world?',
                answer='Billions',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.MASTERED
            ),
            Card(
                question='How do you make pizza?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='How do you makasdse pizsadsandkaza?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='How do you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='Howwewew do you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='How wefiewbfiw you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='ewrknerlw do you masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='How do ewfeownfewo masdsadadaake sdad?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
            Card(
                question='How do you masdsadadaake ewfnewofnoew?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                last_review_date=time.isoformat(),
                learning_status=Card.CardStatusOptions.STRUGGLING
            ),
        ])

    def setUp(self):
        self.client.force_authenticate(user=self.user)

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

    def test_create_card(self):
        print("==================== Create Cards ====================")
        url = reverse('get-create-cards')
        data = {
            'question': 'how many days are in a week',
            'answer': '7',
            'deck_id': Deck.objects.last().pk,
            'scheduled_date': timezone.now().isoformat()
        }

        response = self.client.post(url, data, format='json')        
        self.assertNotEqual(response.status_code, status.HTTP_200_OK, f"Error: {response.data}")
        print(response.data)

    # For gathering all cards for review
    def test_get_cards(self):
        print("==================== Get Cards For Review ====================")
        url = reverse('due-cards')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f'Status code error: {response.data}')
        # self.assertNotIn(self.cards[1].pk, [obj['id'] for obj in response.data], f'Card not found: {response.data}')
        print(response.data)

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
            AuthUser.objects.get(email=self.user.email).xp > 0,
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