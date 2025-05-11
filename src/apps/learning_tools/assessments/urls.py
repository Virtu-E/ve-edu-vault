from django.urls import path

from .views import (
    AssessmentStartView,
    AssessmentCompletionView,
    ActiveAssessmentView,
)

app_name = "assessments"

urlpatterns = [
    path(
        "<str:block_id>/active/",
        ActiveAssessmentView.as_view(),
        name="assessments-active",
    ),
    path(
        "<str:block_id>/start/",
        AssessmentStartView.as_view(),
        name="assessments-start",
    ),
    path(
        "<str:assessment_id>/complete/",
        AssessmentCompletionView.as_view(),
        name="assessments-complete",
    ),
]
