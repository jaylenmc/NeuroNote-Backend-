from rest_framework import serializers
from .models import UPSUserInteraction, DFBLUserInteraction
from flashcards.models import Card
from tests.models import Quiz, Question, Answer, UserAnswer, QuizAttempt

class DFBLSerializer(serializers.Serializer):
    user_answer = serializers.CharField()
    card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    tutor_style = serializers.ChoiceField(choices=DFBLUserInteraction.TutorStyle.choices)
    layer = serializers.IntegerField()

    def create(self, validated_data):
        data = DFBLUserInteraction.objects.create(
        user=self.context.get('request').user,
        neuro_response=validated_data.get('neuro_response'),
        card=validated_data.get('card'),
        attempts=validated_data.get('attempts'),
        tutor_style=validated_data.get('tutor_style'),
        layer=validated_data.get('layer')
        )
        return data

class TestGenerator(serializers.Serializer):
    user_prompt = serializers.CharField()
    question_num = serializers.IntegerField()
    preferred_quiz_type = serializers.CharField()

    quiz_title = serializers.CharField(required=False)
    quiz_subject = serializers.CharField(required=False)
    quiz_type = serializers.CharField(required=False)
    questions = serializers.ListField(required=False)

    def validate_preferred_quiz_type(request, value):
        if value not in ['wr', 'mc', 'wrmc']:
            raise serializers.ValidationError("Availabe choice for quiz type is -> wr, mc, wrmc")
        
    def create(self, validated_data):
        quiz = Quiz.objects.create(
            topic=validated_data["quiz_title"],
            subject=validated_data['quiz_subject'],
            user=self.context['user']
        )

        for q in validated_data['questions']:
            if q['question_type'] == 'wr':
                question = Question.objects.create(
                    quiz=quiz,
                    question_input=q['question'],
                    question_type=q['question_type']
                )
                
                Answer.objects.create(
                    question=question,
                    answer_input=q['answer']
                )
            elif q['question_type'] == 'mc':
                question = Question.objects.create(
                    quiz=quiz,
                    question_input=q['question'],
                    question_type=q['question_type']
                )
                for answer in q['answers']:
                    Answer.objects.create(
                        question=question,
                        answer_input=answer['answer'],
                        is_correct=answer['is_correct']
                    )