from django.urls import path

from .views import (CourseOutlinePathView, GetQuestionAttemptView,
                    GetQuestionsView, GetSingleQuestionAttemptView,
                    PostQuestionAttemptView, QuizCompletionView,
                    iframe_id_given_topic_id)

app_name = "course_ware"

urlpatterns = [
    path(
        "get_questions/<str:username>/<str:block_id>/",
        GetQuestionsView.as_view(),
        name="get_questions_view",
    ),
    path(
        "complete_quiz/",
        QuizCompletionView.as_view(),
        name="complete_quiz",
    ),
    path(
        "post_question_attempt/",
        PostQuestionAttemptView.as_view(),
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
        "get_iframe_id/<str:topic_id>/",
        iframe_id_given_topic_id,
        name="get_iframe_id",
    ),
    path(
        "outline/<str:course_id>/sequential/<str:sequential_id>/path/",
        CourseOutlinePathView.as_view(),
        name="course-sequential-path",
    ),
]
