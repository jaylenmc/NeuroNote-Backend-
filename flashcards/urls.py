from django.urls import path
from . import views
from .study_queue_views import (
    StudyQueueCardAddView,
    StudyQueueCardRemoveView,
    StudyQueueCurrentView,
    StudyQueueDetailView,
    StudyQueueStartView,
)

urlpatterns = [
    # Deck endpoints
    path('deck/', views.DeckCollection.as_view(), name='get-all-decks'),
    path('deck/<int:deck_id>/', views.DeckCollection.as_view(), name='get-specific-deck'),
    # Card endpoints
    path('cards/', views.CardCollection.as_view(), name='get-post-cards'),
    path('cards/<int:deck_id>/', views.CardCollection.as_view(), name='get-cards'),
    path('cards/delete/<int:deck_id>/<int:card_id>/', views.CardCollection.as_view(), name='delete-cards'),
    path('cards/update/<int:deck_id>/<int:card_id>/', views.CardCollection.as_view(), name="put-card"),
    path('cards/due/', views.DueCardsView.as_view(), name='due-cards'),
    # Study Queue (Phase 1 SRS)
    path('study-queue/current/', StudyQueueCurrentView.as_view(), name='study-queue-current'),
    path('study-queue/start/', StudyQueueStartView.as_view(), name='study-queue-start'),
    path('study-queue/<int:group_id>/', StudyQueueDetailView.as_view(), name='study-queue-detail'),
    path('study-queue/cards/', StudyQueueCardAddView.as_view(), name='study-queue-card-add'),
    path('study-queue/cards/<int:card_id>/', StudyQueueCardRemoveView.as_view(), name='study-queue-card-remove'),
    # Review endpoints
    path('review/', views.review_card, name='review-card'),
    # Doing + Feedback Loop endpoints
    path('doing-feedback-review/', views.DoingFeedbackLoopReview.as_view(), name='dfbl-review'),
    path('doing-feedback-review/<int:card_id>/', views.DoingFeedbackLoopReview.as_view(), name='dfbl-review-get'),
]