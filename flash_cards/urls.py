from django.urls import path

from .views import FlashcardView

urlpatterns = [
    path("topic/<str:block_id>/", FlashcardView.as_view(), name="flashcards"),
]
