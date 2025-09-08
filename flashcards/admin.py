from django.contrib import admin
from .models import Deck, Card
    
admin.site.register((Deck, Card))