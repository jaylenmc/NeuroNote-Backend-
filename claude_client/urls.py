from django.urls import path
from . import client

urlpatterns = [
    path('thinker/', client.thinker_ai),
    path('notetaker/', client.NoteTakerAi.as_view()),
    path('cardsgen/', client.CardsGen.as_view()),
    path('testgen/', client.generate_quiz, name='test-gen'),
    path('doingfeedback/', client.doing_feedback_loop, name='doing_feedback_loop'),
    path('upsexplain/', client.understand_problem_solving, name='understand_problem_solving')
]