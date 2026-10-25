from rest_framework import serializers
from .models import UPSUserInteraction, DFBLUserInteraction
from flashcards.models import Card, Deck
from flashcards.serializers import CardSerializer
from tests.models import Quiz, Question, Answer, UserAnswer, QuizAttempt
import anthropic
import os
from pydantic import BaseModel
from .services import ClaudeException

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_KEY")
) 

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
    user_prompt = serializers.CharField(write_only=True)
    question_num = serializers.IntegerField(write_only=True)
    preferred_quiz_type = serializers.CharField(write_only=True)

    quiz_title = serializers.CharField(required=False)
    quiz_subject = serializers.CharField(required=False)
    quiz_type = serializers.CharField(required=False)
    questions = serializers.ListField(required=False)

    def validate_preferred_quiz_type(request, value):
        if value not in ['wr', 'mc', 'wrmc']:
            raise serializers.ValidationError("Availabe choice for quiz type is -> wr, mc, wrmc")
        return value
        
    def create(self, validated_data):
        quiz = Quiz.objects.create(
            topic=validated_data["quiz_title"],
            subject=validated_data['quiz_subject'],
            quiz_type=validated_data['quiz_type'],
            user=self.context['user']
        )

        for q in validated_data['questions']:
            print(type(q))
            if q['question_type'] == 'wr':
                print(type(q['answer']))
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
                print(type(q['answers']))
                question = Question.objects.create(
                    quiz=quiz,
                    question_input=q['question'],
                    question_type=q['question_type']
                )
                for answer in q['answers']:
                    print(type(answer))
                    Answer.objects.create(
                        question=question,
                        answer_input=answer['answer'],
                        is_correct=answer['is_correct']
                    )
        return quiz

class CardKeysSchema(BaseModel):
    question: str
    answer: str

class CardSchema(BaseModel):
    cards: list[CardKeysSchema]

class CardGenSerializer(serializers.Serializer):
    # Input fields
    prompt = serializers.CharField(write_only=True)
    deck_id = serializers.PrimaryKeyRelatedField(queryset=Deck.objects.all(), write_only=True)
    num_of_cards = serializers.IntegerField(write_only=True)
    # Output fields
    cards = CardSerializer(many=True, read_only=True)

    def create(self, validated_data):
        response = client.messages.parse(
            model="claude-haiku-5-5",
            system=f"Generate {validated_data['num_of_cards']} flashcards.",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": validated_data['prompt']}]
                }
            ],
            output_format=CardSchema
        )
        if response.stop_reason in {"refusal", "max_tokens"}:
            raise ClaudeException(response.stop_reason)

        cards = {'cards': []}
        deck = Deck.objects.get(user=self.context['user'], id=validated_data['deck_id'].id)
        for card in response.parsed_output.cards:
            created_card = Card.objects.create(
                card_deck=deck,
                question=card.question,
                answer=card.answer
            )
            cards['cards'].append(created_card)
        return cards