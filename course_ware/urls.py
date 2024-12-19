from django.urls import path

from . import views

urlpatterns = [
    path(
        "mathematics/", views.mathematics_problem_view, name="mathematics_problem_view"
    ),
]
