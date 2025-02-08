from django.urls import path

from .views import CategoryDetailView, CategoryMasteryView

urlpatterns = [
    path(
        "category/<str:block_id>/",
        CategoryDetailView.as_view(),
        name="category-extension-detail",
    ),
    # path(
    #     "category/<str:block_id>/<str:username>points/",
    #     UserTopicPointsView.as_view(),
    #     name="topic-points",
    # ),
    path(
        "category/<str:block_id>/<str:username>/points/",
        CategoryMasteryView.as_view(),
    ),
]
