from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Card, Deck, ReviewGroup, ReviewGroupCard
from .serializers import ReviewGroupSerializer
from .srs_constants import STUDY_QUEUE_GROUP_SIZE
from .srs_service import (
    bucket_counts_for_user,
    create_study_queue,
    dismiss_study_queue,
    get_active_study_queue,
    refresh_study_queue,
    sync_group_memberships,
)


def _serialize_group(group, user):
    return ReviewGroupSerializer(
        group,
        context={
            "user": user,
            "bucket_counts": bucket_counts_for_user(user),
        },
    ).data


def _card_in_group_scope(group, card):
    if card.card_deck.user_id != group.user_id:
        return False
    if group.scope == ReviewGroup.Scope.ALL_CARDS:
        return True
    return card.card_deck_id == group.deck_id


class StudyQueueCurrentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group = get_active_study_queue(request.user)
        if not group:
            return Response({"Message": "No active Study Queue"}, status=status.HTTP_404_NOT_FOUND)
        sync_group_memberships(group)
        refresh_study_queue(group)
        return Response(_serialize_group(group, request.user), status=status.HTTP_200_OK)

    def delete(self, request):
        group = get_active_study_queue(request.user)
        if not group:
            return Response({"Message": "No active Study Queue"}, status=status.HTTP_404_NOT_FOUND)
        dismiss_study_queue(group)
        return Response({"Message": "Study Queue dismissed"}, status=status.HTTP_200_OK)


class StudyQueueStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        active = get_active_study_queue(user)
        replace_existing = request.data.get("replace_existing", False)

        if active and not replace_existing:
            return Response(
                {"Message": "Active Study Queue exists. Dismiss or pass replace_existing=true."},
                status=status.HTTP_409_CONFLICT,
            )
        if active and replace_existing:
            dismiss_study_queue(active)

        deck_id = request.data.get("deck_id")
        scope_param = request.data.get("scope")
        group_size = int(request.data.get("group_size", STUDY_QUEUE_GROUP_SIZE))
        is_timed = bool(request.data.get("is_timed", False))
        timer_seconds = request.data.get("timer_seconds")

        if deck_id and scope_param == "all_cards":
            return Response(
                {"Message": "Provide deck_id or scope all_cards, not both."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if deck_id:
            deck = get_object_or_404(Deck, id=deck_id, user=user)
            group = create_study_queue(
                user,
                scope=ReviewGroup.Scope.SINGLE_DECK,
                deck=deck,
                group_size=group_size,
                is_timed=is_timed,
                timer_seconds=timer_seconds,
            )
        elif scope_param == "all_cards":
            group = create_study_queue(
                user,
                scope=ReviewGroup.Scope.ALL_CARDS,
                deck=None,
                group_size=group_size,
                is_timed=is_timed,
                timer_seconds=timer_seconds,
            )
        else:
            return Response(
                {"Message": "deck_id or scope=all_cards is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(_serialize_group(group, user), status=status.HTTP_200_OK)


class StudyQueueDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(
            ReviewGroup,
            id=group_id,
            user=request.user,
            group_type=ReviewGroup.GroupType.STUDY_QUEUE,
        )
        if group.status != ReviewGroup.Status.ACTIVE:
            return Response({"Message": "Study Queue is not active"}, status=status.HTTP_400_BAD_REQUEST)
        sync_group_memberships(group)
        refresh_study_queue(group)
        return Response(_serialize_group(group, request.user), status=status.HTTP_200_OK)


class StudyQueueCardAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group = get_active_study_queue(request.user)
        if not group:
            return Response({"Message": "No active Study Queue"}, status=status.HTTP_404_NOT_FOUND)
        sync_group_memberships(group)

        card_id = request.data.get("card_id")
        if not card_id:
            return Response({"Message": "card_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        card = get_object_or_404(Card, id=card_id, card_deck__user=request.user)
        if not _card_in_group_scope(group, card):
            return Response({"Message": "Card outside Study Queue scope"}, status=status.HTTP_400_BAD_REQUEST)

        if group.memberships.filter(card=card).exists():
            refresh_study_queue(group)
            return Response(_serialize_group(group, request.user), status=status.HTTP_200_OK)

        ReviewGroupCard.objects.create(
            group=group,
            card=card,
            source=ReviewGroupCard.Source.MANUAL,
        )
        Card.objects.filter(id=card.id).update(is_blacklisted=True)
        refresh_study_queue(group)
        return Response(_serialize_group(group, request.user), status=status.HTTP_200_OK)


class StudyQueueCardRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, card_id):
        group = get_active_study_queue(request.user)
        if not group:
            return Response({"Message": "No active Study Queue"}, status=status.HTTP_404_NOT_FOUND)
        sync_group_memberships(group)
        deleted, _ = group.memberships.filter(card_id=card_id).delete()
        if not deleted:
            return Response({"Message": "Card not in Study Queue"}, status=status.HTTP_404_NOT_FOUND)
        Card.objects.filter(id=card_id).update(is_blacklisted=False)
        refresh_study_queue(group)
        return Response(_serialize_group(group, request.user), status=status.HTTP_200_OK)
