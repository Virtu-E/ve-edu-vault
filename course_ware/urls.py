from django.urls import path

from . import views

urlpatterns = [
    path(
        "get_questions/<str:username>/<str:block_id>",
        views.GetQuestionsView.as_view(),
        name="problem_view",
    ),
    path(
        "post_question_attempt",
        views.PostQuestionAttemptView.as_view(),
        name="post_question_attempt_view",
    ),
    path(
        "get_question_attempt/<str:username>/<str:block_id>/<str:question_id>",
        views.GetQuestionAttemptView.as_view(),
        name="get_question_attempt_view",
    ),
]
