from django.urls import path

from course_ware.factory_views import (
    get_questions_view_factory,
    post_question_attempt_view_factory,
)
from course_ware.views import GetQuestionAttemptView

app_name = "course_ware"

urlpatterns = [
    path(
        "get_questions/<str:username>/<str:block_id>",
        get_questions_view_factory(),
        name="problem_view",
    ),
    path(
        "post_question_attempt",
        post_question_attempt_view_factory(),
        name="post_question_attempt_view",
    ),
    path(
        "get_question_attempt/<str:username>/<str:block_id>/<str:question_id>",
        GetQuestionAttemptView.as_view(),
        name="get_question_attempt_view",
    ),
]
