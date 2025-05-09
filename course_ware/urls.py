from django.urls import include, path

from .views import (
    AssessmentCompletionView,
    AssessmentStartView,
    CourseOutlinePathView,
    GetQuestionAttemptView,
    GetQuestionsView,
    HasActiveAssessmentView,
    PostQuestionAttemptView,
    get_edx_content_view,
    get_learning_objectives,
)

app_name = "course_ware"

# Assessment and Questions endpoints
question_patterns = [
    path(
        "users/<str:username>/objective/<str:block_id>/questions/",
        GetQuestionsView.as_view(),
        name="questions-list",
    ),
    path(
        "assessment/completion/",
        AssessmentCompletionView.as_view(),
        name="assessment-completion",
    ),
    path(
        "users/<str:username>/objective/<str:block_id>/assessment/start/",
        AssessmentStartView.as_view(),
        name="assessment-start",
    ),
    path(
        "users/<str:username>/objective/<str:block_id>/assessment/active/",
        HasActiveAssessmentView.as_view(),
        name="assessment-get-active",
    ),
]

# Question attempts endpoints
attempt_patterns = [
    path(
        "question-attempt/",
        PostQuestionAttemptView.as_view(),
        name="question-attempt-create",
    ),
    path(
        "users/<str:username>/objectives/<str:block_id>/attempts/",
        GetQuestionAttemptView.as_view(),
        name="question-attempts-list",
    ),
]

# Course structure endpoints
course_patterns = [
    path(
        "courses/<str:course_id>/sequentials/<str:sequential_id>/path/",
        CourseOutlinePathView.as_view(),
        name="course-sequential-path",
    ),
]

# Learning content endpoints
content_patterns = [
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

# Main URL patterns
urlpatterns = [
    path("", include(question_patterns)),
    path("", include(attempt_patterns)),
    path("", include(course_patterns)),
    path("", include(content_patterns)),
]
