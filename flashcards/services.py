from .models import ReviewLog, Card, Deck
from django.utils import timezone
from datetime import timedelta

def num_of_cards(deck):
    num = Card.objects.filter(card_deck=deck).count()
    deck.num_of_cards = num
    deck.save()
    return num

def deck_mastery_progress(user, deck_id):
    deck = Deck.objects.filter(user=user, id=deck_id).prefetch_related("card_deck").first()
    mastered_cards = [card for card in deck.card_deck.all() if card.learning_status == Card.CardStatusOptions.MASTERED]
    deck_mstrd_progress = (len(mastered_cards) / deck.card_deck.all().count()) * 100 if deck.card_deck.all().count() > 0 else 0
    deck.mastery_progress = deck_mstrd_progress

    if int(deck_mstrd_progress) == 100:
        deck.is_mastered = True
    else:
        deck.is_mastered = False
    deck.save()
    
    return deck