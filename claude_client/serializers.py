from rest_framework import serializers
from .models import UPSUserInteraction, DFBLUserInteraction
from flashcards.models import Card

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