from django.urls import path

from .views import (
    CourseOutlinePathView,
    GetQuestionAttemptView,
    GetQuestionsView,
    GetSingleQuestionAttemptView,
    PostQuestionAttemptView,
    QuizCompletionView,
    get_edx_content_view,
    get_learning_objectives,
    iframe_id_given_sub_topic_id,
)

app_name = "course_ware"

urlpatterns = [
    # Questions endpoints
    path(
        "users/<str:username>/subtopics/<str:block_id>/questions/",
        GetQuestionsView.as_view(),
        name="questions-list",
    ),
    path(
        "quizzes/completion/",
        QuizCompletionView.as_view(),
        name="quiz-completion",
    ),
    # Question attempts endpoints
    path(
        "question-attempts/",
        PostQuestionAttemptView.as_view(),
        name="question-attempt-create",
    ),
    path(
        "users/<str:username>/subtopics/<str:block_id>/questions/<str:question_id>/attempts/",
        GetSingleQuestionAttemptView.as_view(),
        name="question-attempt-detail",
    ),
    path(
        "users/<str:username>/subtopics/<str:block_id>/attempts/",
        GetQuestionAttemptView.as_view(),
        name="question-attempts-list",
    ),
    # Topic and iframe endpoints
    path(
        "topics/<str:topic_id>/iframe/",
        iframe_id_given_sub_topic_id,
        name="sub_topic-iframe",
    ),
    # Course outline endpoints
    path(
        "courses/<str:course_id>/sequentials/<str:sequential_id>/path/",
        CourseOutlinePathView.as_view(),
        name="course-sequential-path",
    ),
    # Learning objectives endpoints
    path(
        "subtopics/<str:block_id>/objectives/",
        get_learning_objectives,
        name="subtopic-objectives",
    ),
    path(
        "subtopics/<str:block_id>/resources/",
        get_edx_content_view,
        name="get_edx_content",
    ),
]
