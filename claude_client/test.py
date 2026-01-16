from rest_framework.test import APITestCase, force_authenticate
from django.urls import reverse
from authentication.models import AuthUser
from rest_framework import status
from .models import DFBLUserInteraction, UPSUserInteraction
from django.contrib.auth import get_user_model
from flashcards.models import Deck, Card
from unittest.mock import patch
from tests.models import Quiz

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

    def test_generate(self):
        url = reverse('test-gen')

        print("------------------------------------------- QT: Written -------------------------------------------")
        data = {
            "user_prompt": "Django basics",
            "question_num": "3",
            "preferred_quiz_type": "wr"
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            msg=f"Status code error: {response.data}"
        )
        self.assertIsNotNone(
            Quiz.objects.filter(user=self.user)
        )
        print(Quiz.objects.filter(user=self.user))
        print(response.data)

        print("------------------------------------------- QT: Multiple Choice -------------------------------------------")
        data2 = {
            "user_prompt": "Django basics",
            "question_num": "2",
            "preferred_quiz_type": "mc"
        }
        response2 = self.client.post(url, data=data2, format="json")
        self.assertEqual(
            response2.status_code, 
            status.HTTP_200_OK, 
            msg=f"Status code error: {response2.data}"
        )
        self.assertIsNotNone(
            Quiz.objects.filter(user=self.user)
        )
        print(Quiz.objects.filter(user=self.user))
        print(response2.data)

        print("------------------------------------------- QT: Written/Multiple Choice -------------------------------------------")
        data3 = {
            "user_prompt": "Django basics",
            "question_num": "3",
            "preferred_quiz_type": "wrmc"
        }
        response3 = self.client.post(url, data=data3, format="json")
        self.assertEqual(
            response3.status_code, 
            status.HTTP_200_OK, 
            msg=f"Status code error: {response3.data}"
        )
        self.assertIsNotNone(
            Quiz.objects.filter(user=self.user)
        )
        print(Quiz.objects.filter(user=self.user))
        print(response3.data)

    # @patch('claude_client.client.client.messages.create')
    def doing_feedback_loop(self):
        # mock_message = type(
        #     "ClaudeMessage",
        #     (),
        #     {
        #         "content": [
        #             type("Block", (), {"text": "AI Response"})
        #         ]
        #     }
        # )
        # mock_post.return_value = mock_message


        print(f'================== First Iteration ===================')
        url = reverse("doing_feedback_loop")
        data = {
            "card": self.card1.pk,
            "tutor_style": "strict",
            "user_answer": "Its the study of human cognitive activity",
            "layer": 2
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(f"Response: {response.data}")

        # ==================== Second Iteration ===================="
        print(f'================== Second Iteration ===================')
        dfbl_interaction = DFBLUserInteraction.objects.filter(user=self.user)
        new_data2 = {
            "card": self.card1.pk,
            "tutor_style": "strict",
            "user_answer": "Roblox is the coolest game ever",
            "layer": 2
        }
        response2 = self.client.post(url, data=new_data2, format='json')
        self.assertEqual(
            response2.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response2.data}"
        )
        self.assertTrue(
            all(dfbl_interaction.card.question == self.card1.question for dfbl_interaction in dfbl_interaction),
            msg=f"Conversation history isn't the same: {response2.data}"
        )
        print(f"Response2: {response2.data}")

        # ==================== Get Test for attempts ====================
        print(f"============== Attempts ==============")
        url = reverse("doing_feedback_loop", args=[self.card1.pk])
        response4 = self.client.get(url, format='json')
        self.assertEqual(
            response4.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response4.data}"
        )
        self.assertTrue(
            DFBLUserInteraction.objects.filter(user=self.user, card=self.card1).last().attempts == 2,
            msg=f"Attempts didn't increase: {response4.data}"
        )
        print(f"Response4: {response4.data}")

        # ==================== Final Iteration ====================
        print(f'================== Final Iteration ===================')
        new_data3 = {
            "card": self.card2.pk,
            "tutor_style": "strict",
            "user_answer": "Minecraft is the coolest game ever",
            "layer": 1
        }

        response3 = self.client.post(url, data=new_data3, format='json')
        self.assertEqual(
            response3.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response3.data}"
        )
        self.assertTrue(
            DFBLUserInteraction.objects.filter(user=self.user).count() == 1 and DFBLUserInteraction.objects.filter(user=self.user).last().card.question == self.card2.question,
            msg=f"Conversation history didn't delete:"
        )
        print(f"DFBLUserInteraction: {DFBLUserInteraction.objects.filter(user=self.user)}")

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