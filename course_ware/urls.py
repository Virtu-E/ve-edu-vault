from django.urls import include, path

from .views import (
    AssessmentCompletionView,
    AssessmentStartView,
    CourseOutlinePathView,
    QuestionAttemptListView,
    QuestionAttemptsCreateView,
    QuestionsListView,
    ActiveAssessmentView,
    EdxContentView,
    LearningObjectivesView,
)

app_name = "course_ware"

# Assessment endpoints
assessment_patterns = [
    path(
        "assessments/<str:block_id>/active/",
        ActiveAssessmentView.as_view(),
        name="assessments-active",
    ),
    path(
        "assessments/<str:block_id>/start/",
        AssessmentStartView.as_view(),
        name="assessments-start",
    ),
    path(
        "assessments/<str:assessment_id>/complete/",
        AssessmentCompletionView.as_view(),
        name="assessments-complete",
    ),
]

# Question endpoints
question_patterns = [
    path(
        "objectives/<str:block_id>/questions/",
        QuestionsListView.as_view(),
        name="questions-list",
    ),
]

# Question attempts endpoints
attempt_patterns = [
    path(
        "question-attempts/",
        QuestionAttemptsCreateView.as_view(),
        name="question-attempts-create",
    ),
    path(
        "objectives/<str:block_id>/question-attempts/",
        QuestionAttemptListView.as_view(),
        name="question-attempts-list",
    ),
]

# Course structure endpoints
course_patterns = [
    path(
        "courses/<str:course_id>/sequentials/<str:sequential_id>/path/",
        CourseOutlinePathView.as_view(),
        name="course-paths",
    ),
]

# Learning content endpoints
content_patterns = [
    path(
        "subtopics/<str:block_id>/objectives/",
        LearningObjectivesView.as_view(),
        name="subtopic-objectives",
    ),
    path(
        "subtopics/<str:block_id>/resources/",
        EdxContentView.as_view(),
        name="subtopic-resources",
    ),
]

# Main URL patterns
urlpatterns = [
    path("api/v1/", include(assessment_patterns)),
    path("api/v1/", include(question_patterns)),
    path("api/v1/", include(attempt_patterns)),
    path("api/v1/", include(course_patterns)),
    path("api/v1/", include(content_patterns)),
]
