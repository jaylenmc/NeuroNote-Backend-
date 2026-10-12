from django.contrib import admin
from .models import Card, Deck, ReviewGroup, ReviewGroupCard

admin.site.register((Deck, Card, ReviewGroup, ReviewGroupCard))