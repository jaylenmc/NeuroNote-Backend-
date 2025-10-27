from rest_framework.test import APITestCase, force_authenticate
from django.urls import reverse
from authentication.models import AuthUser
from rest_framework import status
from .models import DFBLUserInteraction

class ClaudeTestCase(APITestCase):
    def setUp(self):
        self.user = AuthUser.objects.create(email='bob@testmail.com')
        self.client.force_authenticate(user=self.user)

    def test_generate_test(self):
        url = reverse('test-gen')
        response = self.client.post(url, data={"prompt": "Make a quiz for django basics"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=f"Status code error: {response.data}")
        self.assertTrue(isinstance(response.data, dict), msg=f"Response not dict: {response.data}")

    def doing_feedback_loop(self):
        url = reverse("doing_feedback_loop")
        neuro_responses = ["completly incorrect! ARE YOU EVEN TAKING THIS SERIOUS?!?"]
        user_answers = ["Its the study of everyday human life", "Its the study of human cognitive activity", "Its how chickens can physcially morph into cows", "Its how politics affect the world", "How even the number 10 is"]
        for i in range(5):
            print(f"==================== {i} Iteration ====================")
            data = {
                "question": "What is cultural studies",
                "correct_answer": "An interdisciplinary field that examines how culture is created, how it shapes human experiences, and how it relates to power structures",
                "user_answer": user_answers[i],
                "attempt_count": i,
            }
            response = self.client.post(url, data=data, format='json')
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"Status code error: {response.data}"
            )
            neuro_responses.append(response.data)
            print(response.data)
        print("==================== Final Iteration ====================")
        print(f"DFBLUserInteraction (Before): {DFBLUserInteraction.objects.filter(user=self.user)}")
        new_data = {
           "question": "What is cultural studies",
            "correct_answer": "An interdisciplinary field that examines how culture is created, how it shapes human experiences, and how it relates to power structures",
            "user_answer": "Minecraft is the coolest game ever",
            "attempt_count": 0,
        }

        response2 = self.client.post(url, data=new_data, format='json')
        self.assertEqual(
            response2.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response2.data}"
        )
        self.assertTrue(
            DFBLUserInteraction.objects.filter(user=self.user).count() == 1,
            msg=f"Conversation history didn't delete: {response2.data}"
        )
        print(f"DFBLUserInteraction: {DFBLUserInteraction.objects.filter(user=self.user)}")
        print(f"Response type: {response2.data}")

    def ups_explain(self):
        url = reverse("ups_explain")
        data = {
            "question": "What is cultural studies",
            "correct_answer": "An interdisciplinary field that examines how culture is created, how it shapes human experiences, and how it relates to power structures",
            "user_answer": "Minecraft is the coolest game ever",
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(
            response.status_code, 
            status.HTTP_200_OK, 
            msg=f"Status code error: {response.data}"
            )
        print(response.data)