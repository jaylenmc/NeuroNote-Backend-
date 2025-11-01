from rest_framework.test import APITestCase, force_authenticate
from django.urls import reverse
from authentication.models import AuthUser
from rest_framework import status
from .models import DFBLUserInteraction, UPSUserInteraction

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