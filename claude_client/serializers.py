from rest_framework import serializers
from .models import UPSUserInteraction, DFBLUserInteraction
from flashcards.models import Card

class UPSSerializer(serializers.Serializer):
    user_answer = serializers.CharField()
    attempt_count = serializers.IntegerField()
    card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    tutor_style = serializers.ChoiceField(choices=DFBLUserInteraction.TutorStyle.choices)

    def validate_attempt_count(self, data):
        if data < 0:
            raise serializers.ValidationError("Attempt count must be greater than or equal to 0")
        return data

    def create(self, validated_data):
        print(f'User: {self.context.get('request').user}')
        data = DFBLUserInteraction.objects.create(
        user=self.context.get('request').user,
        neuro_response=validated_data.get('neuro_response'),
        card=validated_data.get('card')
        )
        return data