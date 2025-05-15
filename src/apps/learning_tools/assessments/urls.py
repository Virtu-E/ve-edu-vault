from django.urls import path

from .views import (
    ActiveAssessmentView,
    AssessmentCompletionView,
    AssessmentExpiryView,
    AssessmentStartView,
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
    path(
        "<str:assessment_id>/expire/",
        AssessmentExpiryView.as_view(),
        name="assessment-expire",
    ),
]
