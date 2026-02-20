from rest_framework import serializers
from .models import Quiz, Question, Answer, UserAnswer

class QuizSerilizer(serializers.ModelSerializer):
    class Meta:
        fields = ['topic', 'subject', 'folder', 'id']
        model = Quiz

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['question_input', 'question_type', 'id']
        model = Question

class AnswerSerializer(serializers.ModelSerializer):
    question_input = serializers.CharField(source='question.question_input', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    question = serializers.IntegerField(source='question.id', read_only=True)
    
    class Meta:
        fields = ['answer_input', 'is_correct', 'id', 'question_input', 'question_type', 'question']
        model = Answer

class AnswerReviewSerializer(serializers.Serializer):
    answer_input = serializers.CharField()
    answer_status = serializers.CharField(allow_null=True)


class QuestionReviewSerializer(serializers.Serializer):
    question_input = serializers.CharField()
    answers = AnswerReviewSerializer(many=True)

class QuizPatchSerializer(serializers.Serializer):
    topic = serializers.CharField(allow_blank=True, required=False)
    subject = serializers.CharField(allow_blank=True, required=False)
    questions = serializers.ListField(child=serializers.DictField())

    def validate_questions(self, value):
        for question in value:
            if 'id' in question:
                if not isinstance(question['id'], int):
                    raise serializers.ValidationError("Question id must be an integer")

            if not 'question_input' in question:
                raise serializers.ValidationError("Question input is required")

            if not 'question_type' in question:
                raise serializers.ValidationError("Question type is required")
            if not question['question_type'] in ['MC', 'WR']:
                raise serializers.ValidationError("Question type must be either MC or WR")

            if not 'answers' in question:
                raise serializers.ValidationError("Answers are required")
            for answer in question['answers']:
                if 'id' in answer:
                    if not isinstance(answer['id'], int):
                        raise serializers.ValidationError("Answer id must be an integer")
                if not 'answer_input' in answer:
                    raise serializers.ValidationError("Answer input is required")

                if not 'is_correct' in answer:
                    raise serializers.ValidationError("Answer is correct is required")
                if not isinstance(answer['is_correct'], bool):
                    raise serializers.ValidationError("Answer is correct must be a boolean")
        return value