from .models import Card, Deck
from .srs_constants import MASTERED_BUCKETS
from rest_framework.exceptions import APIException
from rest_framework import status


def num_of_cards(deck):
    num = Card.objects.filter(card_deck=deck).count()
    deck.num_of_cards = num
    deck.save()
    return num

class ConflictError(APIException):  
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Deck with this title already exists"
    default_code = "deck_title_conflict"

    def __repr__(self):
        return {"detail": self.default_detail, "code": self.default_code}