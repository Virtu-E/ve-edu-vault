from django.urls import path

from . import views

urlpatterns = [
    path(
        "get_questions/",
        views.GetQuestionsView.as_view(),
        name="mathematics_problem_view",
    ),
]
