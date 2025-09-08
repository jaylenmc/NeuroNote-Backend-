from rest_framework import serializers
from .models import Deck, Card

class ReviewItemSerializer(serializers.Serializer):
    card_id = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    deck_id = serializers.PrimaryKeyRelatedField(queryset=Deck.objects.all())
    quality = serializers.IntegerField(min_value=0, max_value=5)

    def update(self, instance, data):
        instance.update_sm21(data['quality'])
        return "Cards successfully reviewed"

class ReviewSessionInput(serializers.Serializer):
    session_time = serializers.TimeField()
    review = ReviewItemSerializer(many=True)

class DeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ['title', 'subject', 'num_of_cards', 'id']

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'