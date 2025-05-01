"""
URL configuration for edu_vault project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # LTI provider endpoints
    path("lti/", include("lti_provider.urls", namespace="lti_provider")),
    # API v1 endpoints grouped by domain
    path("api/v1/courses/", include("course_ware.urls")),
    path("api/v1/extensions/", include("course_ware_ext.urls")),
    path("api/v1/webhooks/", include("webhooks.urls")),
    path("api/v1/topics/", include("elastic_search.urls")),
    path("api/v1/flashcards/", include("flash_cards.urls")),
]
