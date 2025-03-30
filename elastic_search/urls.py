from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search_topics, name="topic-search"),
]
