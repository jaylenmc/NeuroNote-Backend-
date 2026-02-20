from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Quiz, Question, Answer
from django.urls import reverse
from rest_framework import status

class QuizTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.user = User.objects.create(email='bob@gmail.com')
        self.quiz = Quiz.objects.create(user=self.user, topic='Test Topic', subject='Test Subject')
        self.question = Question.objects.create(quiz=self.quiz, question_input='Test Question', question_type='MC')
        self.answer = Answer.objects.create(question=self.question, answer_input='Test Answer', is_correct=True)
        self.client.force_authenticate(user=self.user)

    def test_create_quiz(self):
        url = reverse('edit-quiz', args=[self.quiz.id])
        data = {
            'topic': 'A Whole Different TOpic',
            'subject': 'Test Subject',
            'questions': [
                {
                    'question_input': 'Something Else Entirely Different',
                    'question_type': 'MC',
                    'id': self.question.id,
                    'answers': [
                        {
                            'id': self.answer.id,
                            'answer_input': 'Test Answer',
                            'is_correct': True
                        }
                    ]
                }
            ]
        }
        print('-------------------------------- Before Patching --------------------------------')
        print(Quiz.objects.filter(user=self.user).first().topic)
        print([question.question_input for question in Quiz.objects.filter(user=self.user).first().questions.all()])
        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
             status.HTTP_200_OK,
             msg=f"Status code error: {response.data}"
             )
        self.assertEqual(Quiz.objects.count(), 1)
        print(response.data)
        print('-------------------------------- After Patching --------------------------------')
        print(Quiz.objects.filter(user=self.user).first().topic)
        print([question.question_input for question in Quiz.objects.filter(user=self.user).first().questions.all()])