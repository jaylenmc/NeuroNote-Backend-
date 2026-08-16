from neuro_profile.models import NeuroProfile
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import Deck, Card, ReviewLog, DoingFeedbackReview
from rest_framework.response import Response
from rest_framework.exceptions import status
from .serializers import DeckSerializer, CardSerializer, DoingFeedbackReviewSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from achievements.models import UserAchievements
from achievements.services import knowledge_engineer, memory_architect, deck_destroyer
from django.utils import timezone
from .services import num_of_cards, deck_mastery_progress
from django.db.models import Q
from datetime import timedelta
from .serializers import ReviewSessionInput, ReviewItemSerializer, DoingFeedbackReviewModelSerializer
from datetime import timedelta
from django.shortcuts import get_object_or_404

class DeckCollection(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, deck_id=None):
        if deck_id:
            deck = get_object_or_404(Deck, user=request.user, id=deck_id)
            num_of_cards(deck)
            new_deck = deck_mastery_progress(request.user, deck.id)

            serialized = DeckSerializer(new_deck).data
            return Response(serialized, status=status.HTTP_200_OK)

        decks = Deck.objects.filter(user=request.user)
        if decks.exists():
            updated_decks = []
            for deck in decks:
                num_of_cards(deck)
                new_deck = deck_mastery_progress(request.user, deck.id)
                updated_decks.append(new_deck)

            user = get_user_model().objects.filter(email=request.user.email).first()
            neuro_profile = NeuroProfile.objects.get(user=user)
            serialized = DeckSerializer(updated_decks, many=True)

            data = {
                'decks': serialized.data,
                'xp': neuro_profile.xp
            }

            return Response(data, status=status.HTTP_200_OK)
        return Response({"Error": "User doesn't have decks"}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        title = request.data.get('title')
        user = get_user_model().objects.filter(email=request.user.email).first()
        subject = request.data.get('subject')

        if Deck.objects.filter(title__iexact=title).exists():
            return Response({"Message": "Already have card with title"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            user_collection = Deck.objects.create(title=title, user=user, subject=subject)
        
        serialized = DeckSerializer(user_collection)
        deck_destroyer(user=user)

        return Response(serialized.data, status=status.HTTP_200_OK)
    
    def put(self, request, deck_id):
        deck = Deck.objects.filter(user=request.user, id=deck_id).first()
        if not deck:
            return Response({"Message": "Deck does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        title = request.data.get('title')
        subject = request.data.get('subject')

        if title:
            deck.title = title
        if subject:
            deck.subject = subject

        deck.save()
        serialized = DeckSerializer(deck)

        return Response(serialized.data, status=status.HTTP_200_OK)
    
    def delete(self, request ,deck_id):
        id = deck_id
        user = request.user
        deck_collection = Deck.objects.filter(user_id=user)

        if not deck_collection.filter(id=id).exists():
            return Response("Deck does not exists", status=status.HTTP_404_NOT_FOUND)
        deck = deck_collection.filter(id=id).first()
        deck.delete()

        return Response({"Message": 'Deck successfully deleted'}, status=status.HTTP_200_OK)
    
class CardCollection(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, deck_id=None):
        if deck_id:
            cards = Card.objects.filter(card_deck__user=request.user, card_deck__id=deck_id)
            serialized = CardSerializer(cards, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)

        cards = Card.objects.filter(card_deck__user=request.user)
        serialized = CardSerializer(cards, many=True)

        return Response(serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        input_data = CardSerializer(data=request.data)
        input_data.is_valid(raise_exception=True)
        card_data = input_data.save()

        serialized = CardSerializer(card_data)
        fixed_serializer = dict(serialized.data)
        fixed_serializer["last_review_date"] = "None"

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
    if card_input_serializer.is_valid():
        validated_data = card_input_serializer.validated_data
        duration = timedelta(
            hours=validated_data['session_time'].hour, 
            minutes=validated_data['session_time'].minute,
            seconds=validated_data['session_time'].second
            )
        review_log = ReviewLog.objects.create(user=request.user, session_time=duration)

        for card_info in validated_data['review']:
            instance = Card.objects.get(
                card_deck__user=request.user, 
                card_deck=card_info["deck_id"],
                id=card_info["card_id"].id,
                )
            
            card_info['deck_id'] = card_info['deck_id'].id
            card_info['card_id'] = card_info['card_id'].id

            card_input_serializer = ReviewItemSerializer(instance=instance, data=card_info, partial=True, context={"user": request.user})
            card_input_serializer.is_valid(raise_exception=True)
            card_input_serializer.save()

            review_log.cards.add(instance)

        return Response({"Message": "Cards successfully reviewed"}, status=status.HTTP_200_OK)
    return Response(card_input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DueCardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = Q(card_deck__user=request.user)

        if request.query_params.get('due_soon', 'false').lower() == 'true':
            filters &= Q(scheduled_date__lte=timezone.now() + timedelta(hours=1))
        else:
            filters &= Q(scheduled_date__lte=timezone.now())
          
        due_cards = Card.objects.filter(filters)

        if not due_cards:
            return Response({"Message": "No cards due for review"}, status=status.HTTP_200_OK)
        
        serialized = CardSerializer(due_cards, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

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