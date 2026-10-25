from neuro_profile.models import NeuroProfile
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import Deck, Card, ReviewLog, DoingFeedbackReview, ReviewGroup
from rest_framework.response import Response
from rest_framework.exceptions import status
from .serializers import DeckSerializer, CardSerializer, DoingFeedbackReviewSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from datetime import timedelta
from .serializers import ReviewSessionInput, ReviewItemSerializer, DoingFeedbackReviewModelSerializer
from .srs_service import (
    apply_study_queue_blacklist,
    apply_timeout_ratings,
    bucket_counts_for_user,
    complete_study_queue,
    sync_card_review_group_flags,
    get_active_study_queue,
    group_queue_complete,
    refresh_study_queue,
    sync_group_memberships,
)

class DeckCollection(APIView):
    permission_classes = [IsAuthenticated]

    # Either get a specific deck by "deck_id" or get all decks from the user
    # TODO: Make sure client doesn't expect deck mastery progress
    # TODO: Make sure client doesn't expect neuro profile xp
    def get(self, request, deck_id=None):
        if deck_id:
            deck = Deck.objects.filter(user=request.user, id=deck_id)
            if deck.exists():
                deck = deck.first()
                serialized = DeckSerializer(deck)
                return Response(serialized.data, status=status.HTTP_200_OK)
            return Response({"Message": "Deck doesn't exists"}, status=status.HTTP_404_NOT_FOUND)

        decks = Deck.objects.filter(user=request.user)
        if decks.exists():
            serialized = DeckSerializer(decks, many=True)

            return Response(serialized.data, status=status.HTTP_200_OK)
        return Response({"Error": "User doesn't have decks"}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        deck_serializer = DeckSerializer(data=request.data, context={"user": request.user})
        deck_serializer.is_valid(raise_exception=True)
        deck_serializer.save()

        return Response(deck_serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, deck_id):
        deck = Deck.objects.filter(user=request.user, id=deck_id)

        if not deck.exists():
            return Response({"Message": "Deck does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        deck = deck.first()
        deck_serializer = DeckSerializer(deck, data=request.data, context={"user": request.user})
        deck_serializer.is_valid(raise_exception=True)
        deck_serializer.save()

        return Response(deck_serializer.data, status=status.HTTP_200_OK)
    
    # Either delete a specific deck by "deck_id" or delete all decks from the user
    # TODO: Add bulk delete functionality on client side
    def delete(self, request, deck_id=None):
        if deck_id:
            deck_query_list = Deck.objects.filter(user=request.user, id=deck_id)
            if not deck_query_list.exists():
                return Response({"Message": "Deck does not exist"}, status=status.HTTP_404_NOT_FOUND)
            deck_query_list.delete()
            return Response({"Message": "Deck successfully deleted"}, status=status.HTTP_200_OK)

        if not "deck_ids" in request.data:
            return Response({"Message": "deck_ids is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(request.data.get("deck_ids"), list):
            return Response({"Message": "deck_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)
            
        deck_query_list = Deck.objects.filter(user=request.user, id__in=request.data.get("deck_ids"))
        if not deck_query_list.exists():
            return Response({"Message": "User doesn't have decks"}, status=status.HTTP_404_NOT_FOUND)
        deck_query_list.delete()
        return Response({"Message": 'Deck successfully deleted'}, status=status.HTTP_200_OK)
    
class CardCollection(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, deck_id=None):
        sync_card_review_group_flags(request.user)
        if deck_id:
            cards = Card.objects.filter(card_deck__user=request.user, card_deck__id=deck_id)
            serialized = CardSerializer(cards, many=True, context={"user": request.user})
            return Response(serialized.data, status=status.HTTP_200_OK)

        cards = Card.objects.filter(card_deck__user=request.user)
        serialized = CardSerializer(cards, many=True, context={"user": request.user})

        return Response(serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        input_data = CardSerializer(data=request.data)
        input_data.is_valid(raise_exception=True)
        card_data = input_data.save()

        serialized = CardSerializer(card_data)
        fixed_serializer = dict(serialized.data)
        fixed_serializer["last_review_date"] = None

        return Response(fixed_serializer, status=status.HTTP_200_OK)
    
    def put(self, request, deck_id, card_id):
        card = Card.objects.filter(card_deck__user=request.user, card_deck=deck_id, id=card_id)

        if not card:
            return Response({"Error": "Card doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
        
        serialized = CardSerializer(card.first(), data=request.data)
        serialized.is_valid(raise_exception=True)
        serialized.save()

        return Response(serialized.data, status=status.HTTP_200_OK)
    
    def delete(self, request, deck_id=None, card_id=None):
        if request.query_params.get('bulk_delete'):
            ids = request.query_params.get('bulk_delete')
            ids_nums = [int(id.strip()) for id in ids.split(',') if id.strip().isdigit()]
            Card.objects.filter(card_deck__user=request.user, id__in=ids_nums).delete()
            return Response({'Message': 'Cards successfully deleted'}, status=status.HTTP_200_OK)

        if not Card.objects.filter(card_deck__user=request.user, card_deck=deck_id, id=card_id).exists():
            return Response({"Message": 'Card doesnt exists'}, status=status.HTTP_404_NOT_FOUND)
        
        card = Card.objects.filter(card_deck__user=request.user, card_deck=deck_id, id=card_id).first()
        card.delete()

        return Response({"Message": "Successfully deleted"}, status=status.HTTP_200_OK)
        
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def review_card(request):
    card_input_serializer = ReviewSessionInput(data=request.data, context={"method": request.method})
    if not card_input_serializer.is_valid():
        return Response(card_input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = card_input_serializer.validated_data
    study_group = None
    study_group_id = validated_data.get("study_group_id")
    if study_group_id:
        study_group = ReviewGroup.objects.filter(
            id=study_group_id,
            user=request.user,
            group_type=ReviewGroup.GroupType.STUDY_QUEUE,
            status=ReviewGroup.Status.ACTIVE,
        ).first()
        if not study_group:
            return Response({"Message": "Invalid or inactive study_group_id"}, status=status.HTTP_400_BAD_REQUEST)
        sync_group_memberships(study_group)

    duration = timedelta(
        hours=validated_data['session_time'].hour,
        minutes=validated_data['session_time'].minute,
        seconds=validated_data['session_time'].second,
    )
    review_log = ReviewLog.objects.create(
        user=request.user,
        session_time=duration,
        review_group=study_group,
    )

    reviewed_ratings = []
    reviewed_card_ids = []

    for card_id in validated_data.get("timed_out_card_ids") or []:
        timeout_ratings = apply_timeout_ratings(request.user, [card_id])
        reviewed_ratings.extend(timeout_ratings)
        reviewed_card_ids.extend([card_id for card_id, _ in timeout_ratings])

    for card_info in validated_data['review']:
        instance = Card.objects.get(
            card_deck__user=request.user,
            card_deck=card_info["deck_id"],
            id=card_info["card_id"].id,
        )

        payload = {
            'deck_id': card_info['deck_id'].id,
            'card_id': card_info['card_id'].id,
            'bucket': card_info['bucket'],
        }
        item_serializer = ReviewItemSerializer(
            instance=instance,
            data=payload,
            partial=True,
            context={"user": request.user},
        )
        item_serializer.is_valid(raise_exception=True)
        item_serializer.save()
        reviewed_ratings.append((instance.id, card_info['bucket']))
        reviewed_card_ids.append(instance.id)
        review_log.cards.add(instance)

    if study_group:
        apply_study_queue_blacklist(study_group, reviewed_ratings)
        sync_group_memberships(study_group)
        if group_queue_complete(study_group, reviewed_card_ids):
            complete_study_queue(study_group)
        else:
            refresh_study_queue(study_group)
        sync_card_review_group_flags(request.user)

    return Response({"Message": "Cards successfully reviewed"}, status=status.HTTP_200_OK)

class DueCardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # due_soon retained for API compatibility; Study Queue uses sync/backfill instead of scheduled_date.
        group = get_active_study_queue(request.user)
        bucket_counts = bucket_counts_for_user(request.user)

        if group:
            sync_group_memberships(group)
            refresh_study_queue(group)
            card_ids = group.memberships.values_list("card_id", flat=True)
            due_cards = Card.objects.filter(id__in=card_ids, card_deck__user=request.user)
            serialized = CardSerializer(due_cards, many=True, context={"user": request.user})
            return Response(
                {
                    "cards": serialized.data,
                    "study_group_id": group.id,
                    "bucket_counts": bucket_counts,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"cards": [], "study_group_id": None, "bucket_counts": bucket_counts},
            status=status.HTTP_200_OK,
        )

class DoingFeedbackLoopReview(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, card_id):
        dfbl_review = DoingFeedbackReview.objects.filter(user=request.user, card_id=card_id)
        if dfbl_review.exists():
            return Response({"Message": DoingFeedbackReviewModelSerializer(dfbl_review.first()).data}, status=status.HTTP_200_OK)
        return Response({"Message": "No DFBL review found"}, status=status.HTTP_200_OK)

    # Create and update dfbl review for card user is currently doing during dfbl study session
    def patch(self, request):
        card = Card.objects.get(id=request.data['card'])

        dfbl_review = DoingFeedbackReview.objects.create(user=request.user, card=card)
        dfbl_serializer = DoingFeedbackReviewSerializer(dfbl_review, data=request.data, context={"user": request.user}, partial=True)

        if dfbl_serializer.is_valid():
            dfbl_serializer.save()
            return Response({"Message": "Successfully created DFBL review"}, status=status.HTTP_200_OK)

        return Response(dfbl_serializer.errors, status=status.HTTP_400_BAD_REQUEST)