from django.urls import path

from . import views

urlpatterns = [
    path("launch/", views.lti_launch, name="lti_launch"),
    path("login/", views.lti_login, name="lti_login"),
    path("jwks/", views.jwks_view, name="jwks"),
]
