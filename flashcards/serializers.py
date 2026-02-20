from rest_framework import serializers
from .models import Deck, Card
from .services import deck_mastery_progress
from .models import DoingFeedbackReview

class ReviewItemSerializer(serializers.Serializer):
    card_id = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    deck_id = serializers.PrimaryKeyRelatedField(queryset=Deck.objects.all())
    quality = serializers.IntegerField(min_value=0, max_value=5)

    def update(self, instance, data):
        instance.update_sm21(data['quality'])
        deck_mastery_progress(self.context['user'], data['deck_id'].id)
        return "Cards successfully reviewed"

class ReviewSessionInput(serializers.Serializer):
    session_time = serializers.TimeField()
    review = ReviewItemSerializer(many=True)

class DeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ['title', 'subject', 'num_of_cards', 'id', 'mastery_progress', "is_mastered"]

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'

class DoingFeedbackReviewSerializer(serializers.Serializer):
    card=serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    layer_attempts=serializers.IntegerField(write_only=True)
    layer=serializers.IntegerField(write_only=True)

    def validate_layer(self, value):
        if value not in [1,2,3]:
            raise serializers.ValidationError("Layer must be 1, 2, or 3")
        return value

    def validate_layer_attempts(self, value):
        if value < 0:
            raise serializers.ValidationError("Layer attempts must be greater than 0")
        return value

    def update(self, instance, validated_data):
        if validated_data['layer'] == 1:
            instance.layer_one_attempts = validated_data['layer_attempts']
        elif validated_data['layer'] == 2:
            instance.layer_two_attempts = validated_data['layer_attempts']
        elif validated_data['layer'] == 3:
            instance.layer_three_attempts = validated_data['layer_attempts']
        instance.save()
        return instance

class DoingFeedbackReviewModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'layer_one_attempts', 'layer_two_attempts', 'layer_three_attempts', 'dfbl_attempt_date']
        model = DoingFeedbackReview