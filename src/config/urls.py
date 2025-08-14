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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from oauth2_provider import urls as oauth2_urls
from oauth2_provider.views import TokenView

from src.config.django.dev import STATIC_ROOT, STATIC_URL

# Custom admin site configuration
admin.site.site_header = "VirtuEducate Admin"
admin.site.site_title = "VirtuEducate Admin Portal"
admin.site.index_title = "Welcome to VirtuEducate Administration"

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # LTI provider endpoints
    path(
        "api/v1/lti/",
        include("src.apps.integrations.lti_provider.urls", namespace="lti_provider"),
    ),
    # API v1 endpoints grouped by domain
    path("api/v1/content/", include("src.apps.core.content.urls")),
    path("api/v1/assessments/", include("src.apps.learning_tools.assessments.urls")),
    path("api/v1/questions/", include("src.apps.learning_tools.questions.urls")),
    path("api/v1/extensions/", include("src.apps.content_ext.urls")),
    path("api/v1/webhooks/", include("src.apps.integrations.webhooks.urls")),
    path("api/v1/search/", include("src.apps.core.search.urls")),
    path("api/v1/flashcards/", include("src.apps.learning_tools.flash_cards.urls")),
    path("api/v1/oauth/", include(oauth2_urls)),
    path("oauth2/access_token", TokenView.as_view(), name="token"),
    path("api/v1/auth/", include("src.apps.core.authentication.urls")),
    path("api/v1/user/", include("src.apps.core.users.urls")),
    path("api/v1/user/", include("src.apps.core.users.urls")),
    path("api/v1/timetable/", include("src.apps.learning_tools.time_table.urls")),
    path("api/v1/notifications/", include("src.apps.core.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
