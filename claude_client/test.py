from rest_framework.test import APITestCase, force_authenticate
from django.urls import reverse
from authentication.models import AuthUser
from rest_framework import status
from .models import DFBLUserInteraction, UPSUserInteraction
from django.contrib.auth import get_user_model
from flashcards.models import Deck, Card

class ClaudeTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create_user(email='bob@gmail.com', password='12345')

        cls.deck1 = Deck.objects.create(user=cls.user, title="Test Deck", subject="Test Subject")
        cls.deck2 = Deck.objects.create(user=cls.user, title="Test Deck2", subject="Test Subject2")

        cls.card1 = Card.objects.create(answer='Test Deck', question='Test Subject', card_deck=cls.deck1)
        cls.card2 = Card.objects.create(answer='Test Deck2', question='Test Subject2', card_deck=cls.deck2)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_generate_test(self):
        url = reverse('test-gen')
        response = self.client.post(url, data={"prompt": "Make a quiz for django basics"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=f"Status code error: {response.data}")
        self.assertTrue(isinstance(response.data, dict), msg=f"Response not dict: {response.data}")

    def doing_feedback_loop(self):
        print(f'self cards: {self.card1}')
        url = reverse("doing_feedback_loop")
        data = {
            "card": self.card1.pk,
            "tutor_style": "strict",
            "user_answer": "Its the study of human cognitive activity",
            "attempt_count": 0,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data)
        # print("==================== Final Iteration ====================")
        # print(f"DFBLUserInteraction (Before): {DFBLUserInteraction.objects.filter(user=self.user)}")
        # new_data = {
        # "card": self.card2.pk,
        #     "tutor_style": "strict",
        #     "user_answer": "Minecraft is the coolest game ever",
        #     "attempt_count": 0,
        # }

        # response2 = self.client.post(url, data=new_data, format='json')
        # self.assertEqual(
        #     response2.status_code,
        #     status.HTTP_200_OK,
        #     msg=f"Status code error: {response2.data}"
        # )
        # self.assertTrue(
        #     DFBLUserInteraction.objects.filter(user=self.user).count() == 1,
        #     msg=f"Conversation history didn't delete: {response2.data}"
        # )
        # print(f"DFBLUserInteraction: {DFBLUserInteraction.objects.filter(user=self.user)}")
        # print(f"Response type: {response2.data}")

# ======================================== Understand + Problem Solving Test Case ========================================
    def ups_explain(self):
        # ---------------------------------------- Explanation request ----------------------------------------
        url = reverse("understand_problem_solving")
        data = {
            "question": "What is cultural studies",
            "explanation":  "Minecraft is the coolest game ever"
        }
        query_url = f"{url}?type=explain"
        response = self.client.post(query_url, data=data, format='json')
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            msg=f"Status code error: {response.data}"
            )
        print('==================== Explain Response ====================')
        print(response.data)

# ---------------------------------------- Connection request ----------------------------------------
        data2 = {
            "principles": ["The principles of cultural studies are the study of how culture is created, how it shapes human experiences, and how it relates to power structures"],
            "solution_summary": "Minecraft is the coolest game ever",
            "question": data['question']
        }
        query_url2 = f"{url}?type=connection"
        response2 = self.client.post(query_url2, data=data2, format='json')
        self.assertEqual(
            response2.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response2.data}"
        )
        print('==================== Connection Response ====================')
        print(response2.data)
        print(f"Objects: {UPSUserInteraction.objects.filter(user=self.user)}")
# ----------------- Check if objects delete from new question -----------------
        data3 = {
            "explanation": "hello",
            "question": "Who is spiderman"
        }
        query_url2 = f"{url}?type=explain"
        response3 = self.client.post(query_url2, data=data3, format='json')
        self.assertEqual(
            response2.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response2.data}"
        )
        print(f"Objects2: {UPSUserInteraction.objects.filter(user=self.user)}")
        self.assertNotEqual(
            UPSUserInteraction.objects.filter(user=self.user).first().question,
            data['question'],
            msg=f"Objects didn't delete: {response3.data}"
        )