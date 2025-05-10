from django.urls import path

from .views import (

)

app_name = "assessments"

urlpatterns = [
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
