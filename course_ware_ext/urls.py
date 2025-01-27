from django.urls import path

from .views import CategoryDetailView

urlpatterns = [
    path(
        "category/<str:block_id>/",
        CategoryDetailView.as_view(),
        name="category-extension-detail",
    ),
]
