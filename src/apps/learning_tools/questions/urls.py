from django.urls import path

from .views import (
    QuestionAttemptListView,
    QuestionAttemptsCreateView,
    StudentQuestionSetView,
)

app_name = "questions"

urlpatterns = [
    path(
        "objectives/<str:block_id>/question-attempts/create/",
        QuestionAttemptsCreateView.as_view(),
        name="question-attempts-create",
    ),
    path(
        "objectives/<str:block_id>/question-attempts/",
        QuestionAttemptListView.as_view(),
        name="question-attempts-list",
    ),
    path(
        "objectives/<str:block_id>/questions/",
        StudentQuestionSetView.as_view(),
        name="questions-list",
    ),
]
