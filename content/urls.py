from django.urls import path

from .views import (
    get_edx_resources,
    get_learning_objectives,
)

app_name = "content"

urlpatterns = [
    path(
        "subtopics/<str:block_id>/objectives/",
        get_learning_objectives,
        name="subtopic-objectives",
    ),
    path(
        "subtopics/<str:block_id>/resources/",
        get_edx_resources,
        name="subtopic-resources",
    ),
]
