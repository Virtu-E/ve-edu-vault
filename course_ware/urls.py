from django.urls import path

from course_ware.factory_views import (
    complete_quiz_view_factory,
    get_questions_view_factory,
    post_question_attempt_view_factory,
)
from course_ware.views import (
    GetQuestionAttemptView,
    GetSingleQuestionAttemptView,
    iframe_id_given_topic_id,
)

app_name = "course_ware"

urlpatterns = [
    path(
        "get_questions/<str:username>/<str:block_id>/",
        get_questions_view_factory(),
        name="get_questions_view",
    ),
    path(
        "post_question_attempt/",
        post_question_attempt_view_factory(),
        name="post_question_attempt_view",
    ),
    path(
        "get_question_attempt/<str:username>/<str:block_id>/<str:question_id>/",
        GetSingleQuestionAttemptView.as_view(),
        name="get_single_question_attempt_view",
    ),
    path(
        "get_question_attempt/<str:username>/<str:block_id>/",
        GetQuestionAttemptView.as_view(),
        name="get_question_attempt_view",
    ),
    path(
        "complete_quiz/",
        complete_quiz_view_factory(),
        name="complete_quiz",
    ),
    path(
        "get_iframe_id/<str:topic_id>/",
        iframe_id_given_topic_id,
        name="get_iframe_id",
    ),
]
