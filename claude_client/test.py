from rest_framework.test import APITestCase, force_authenticate
from django.urls import reverse
from rest_framework import status
from .models import DFBLUserInteraction, UPSUserInteraction
from django.contrib.auth import get_user_model
from flashcards.models import Deck, Card
import json
from tests.models import Quiz

class CardGenTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create_user(email='cardgen@gmail.com', password='12345')
        cls.deck = Deck.objects.create(
            user=cls.user,
            title="Card Gen Deck",
            subject="Card Gen Subject",
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    # Currently users don't have allocated tokens; I'm checking against "1000" because it's the max tokens for the model
    def test_card_generation_success(self):
        url = f"{reverse('cards_gen')}?token_check=true"
        num_of_cards = 30
        data = {
            "prompt": "Economics basics",
            "num_of_cards": num_of_cards,
            "deck_id": self.deck.pk,
        }

        response_token_check = self.client.post(url, data=data, format="json")
        response_token_check_data = json.loads(response_token_check.data)
        print(response_token_check_data)
        self.assertEqual(
            response_token_check.status_code, 
            status.HTTP_200_OK,
            msg=f"Status code error: {response_token_check.data}",
            )

        if int(response_token_check_data['input_tokens']) < 1000:
            url = f"{reverse('cards_gen')}?token_check=false"
            response = self.client.post(url, data=data, format="json")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}",
        )
        self.assertIn("cards", response.data)
        cards = response.data["cards"]
        self.assertEqual(
            len(cards),
            num_of_cards,
            msg=f"Expected {num_of_cards} cards, got {len(cards)}: {response.data}",
        )

        CARD_RESPONSE_FIELDS = {
            "id",
            "question",
            "answer",
            "card_deck",
            "bucket",
            "last_review_date",
            "last_reviewed_at",
            "is_blacklisted",
            "slot_label",
        }

        for card in cards:
            self.assertEqual(
                set(card.keys()),
                CARD_RESPONSE_FIELDS,
                msg=f"Card fields mismatch: {card}",
            )
            self.assertEqual(card["card_deck"], self.deck.pk)
            self.assertTrue(card["question"])
            self.assertTrue(card["answer"])
            self.assertIsInstance(card["id"], int)
            self.assertIsInstance(card["is_blacklisted"], bool)

    # Test to catch pydantic validation errors
    def test_card_generation_validation_error(self):
        url = f"{reverse('cards_gen')}?token_check=false"
        data = {
            "prompt": "in depth explanation of the theory of relativity",
            "num_of_cards": 100,
            "deck_id": self.deck.pk,
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
            msg=f"Status code error: {response.data}",
        )
        print(response.data)


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

    def test_cards_gen(self):
        url = reverse('cards_gen')
        data = {
            "prompt": "Django basics",
            "num_of_cards": "3",
            "deck_id": self.deck1.pk
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)

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