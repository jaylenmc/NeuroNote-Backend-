from django.urls import path
from . import client

urlpatterns = [
    path('cardsgen/', client.CardsGen.as_view(), name='cards_gen'),
    path('testgen/', client.generate_quiz, name='test-gen'),
    path('upsexplain/', client.understand_problem_solving, name='understand_problem_solving'),

    path('doingfeedback/', client.DoingFeedbackLoop.as_view(), name='doing_feedback_loop'),
    path('doingfeedback/<int:card_id>/', client.DoingFeedbackLoop.as_view(), name='doing_feedback_loop'),
]