from django.urls import path
from knox.views import LogoutAllView as KnoxLogOutAllView
from knox.views import LogoutView as KnoxLogOutView

from .views import EdxLoginView

app_name = "authentication"

urlpatterns = [
    path(
        "edx_user/token",
        EdxLoginView.as_view(),
        name="edx-user-token",
    ),
    path(
        "edx_user/logout",
        KnoxLogOutView.as_view(),
        name="edx-user-knox-logout",
    ),
    path(
        "edx_user/logout/all",
        KnoxLogOutAllView.as_view(),
        name="edx-user-token",
    ),
]
