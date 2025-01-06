from django.urls import path

from . import views

app_name = "course_ware"

urlpatterns = [
    path(
        "get_questions/<str:username>/<str:block_id>",
        views.get_questions_view_factory(),
        name="problem_view",
    ),
    path(
        "post_question_attempt",
        views.post_question_attempt_view_factory,
        name="post_question_attempt_view",
    ),
    path(
        "get_question_attempt/<str:username>/<str:block_id>/<str:question_id>",
        views.get_question_attempt_view_factory,
        name="get_question_attempt_view",
    ),
]
