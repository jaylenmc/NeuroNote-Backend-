from .models import Card, Deck
from .srs_constants import MASTERED_BUCKETS


def num_of_cards(deck):
    num = Card.objects.filter(card_deck=deck).count()
    deck.num_of_cards = num
    deck.save()
    return num