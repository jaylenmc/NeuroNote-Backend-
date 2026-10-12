from rest_framework import serializers

from .models import Deck, Card, DoingFeedbackReview, ReviewGroup, ReviewGroupCard
from .srs_service import get_slot_label


class ReviewItemSerializer(serializers.Serializer):
    card_id = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    deck_id = serializers.PrimaryKeyRelatedField(queryset=Deck.objects.all())
    bucket = serializers.IntegerField(min_value=1, max_value=4)

    def update(self, instance, validated_data):
        user = self.context["user"]
        bucket = validated_data["bucket"]
        instance.apply_bucket_rating(user, bucket)
        return instance


class ReviewSessionInput(serializers.Serializer):
    session_time = serializers.TimeField()
    review = ReviewItemSerializer(many=True)
    study_group_id = serializers.IntegerField(required=False, allow_null=True)
    timed_out_card_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        if "quality" in self.initial_data:
            raise serializers.ValidationError({"quality": "Use bucket (1-4) per review item instead of quality."})
        for item in self.initial_data.get("review", []):
            if isinstance(item, dict) and "quality" in item:
                raise serializers.ValidationError(
                    {"review": "Each item must use bucket (1-4), not quality."}
                )
        return attrs


class DeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ["title", "subject", "num_of_cards", "id"]


class CardSerializer(serializers.ModelSerializer):
    last_review_date = serializers.DateTimeField(source="last_reviewed_at", read_only=True, allow_null=True)
    slot_label = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = [
            "id",
            "question",
            "answer",
            "card_deck",
            "bucket",
            "last_review_date",
            "last_reviewed_at",
            "is_blacklisted",
            "slot_label",
        ]
        read_only_fields = ["last_reviewed_at", "is_blacklisted", "slot_label"]

    def get_slot_label(self, obj):
        user = self.context.get("user")
        if not user:
            return None
        return get_slot_label(user, obj.id)


class StudyQueueCardSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="card.id")
    question = serializers.CharField(source="card.question")
    answer = serializers.CharField(source="card.answer")
    card_deck = serializers.IntegerField(source="card.card_deck_id")
    bucket = serializers.CharField(source="card.bucket")
    time_in_group = serializers.DateTimeField()
    source = serializers.CharField()
    slot_label = serializers.SerializerMethodField()
    last_review_date = serializers.DateTimeField(source="card.last_reviewed_at", allow_null=True)

    def get_slot_label(self, obj):
        user = self.context.get("user")
        if not user:
            return None
        return get_slot_label(user, obj.card_id)


class ReviewGroupSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    deck_id = serializers.IntegerField(allow_null=True)
    cards = serializers.SerializerMethodField()
    bucket_counts = serializers.SerializerMethodField()

    class Meta:
        model = ReviewGroup
        fields = [
            "id",
            "display_name",
            "group_type",
            "scope",
            "deck_id",
            "status",
            "group_size",
            "is_timed",
            "timer_seconds",
            "created_at",
            "completed_at",
            "cards",
            "bucket_counts",
        ]

    def get_display_name(self, obj):
        return "Study Queue"

    def get_cards(self, obj):
        memberships = obj.memberships.select_related("card").order_by("time_in_group")
        return StudyQueueCardSerializer(
            memberships,
            many=True,
            context=self.context,
        ).data

    def get_bucket_counts(self, obj):
        return self.context.get("bucket_counts", {})


class DoingFeedbackReviewSerializer(serializers.Serializer):
    card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())
    layer_attempts = serializers.IntegerField(write_only=True)
    layer = serializers.IntegerField(write_only=True)

    def validate_layer(self, value):
        if value not in [1, 2, 3]:
            raise serializers.ValidationError("Layer must be 1, 2, or 3")
        return value

    def validate_layer_attempts(self, value):
        if value < 0:
            raise serializers.ValidationError("Layer attempts must be greater than 0")
        return value

    def update(self, instance, validated_data):
        if validated_data["layer"] == 1:
            instance.layer_one_attempts = validated_data["layer_attempts"]
        elif validated_data["layer"] == 2:
            instance.layer_two_attempts = validated_data["layer_attempts"]
        elif validated_data["layer"] == 3:
            instance.layer_three_attempts = validated_data["layer_attempts"]
        instance.save()
        return instance


class DoingFeedbackReviewModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "layer_one_attempts",
            "layer_two_attempts",
            "layer_three_attempts",
            "dfbl_attempt_date",
        ]
        model = DoingFeedbackReview
