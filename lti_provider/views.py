# lti_provider/views.py
from django.http import JsonResponse
from django.urls import reverse
from pylti1p3.contrib.django import DjangoOIDCLogin
from pylti1p3.message_launch import MessageLaunch

from .lti_config import DjangoToolConf
from .models import ToolConsumer


def lti_login(request):
    """
    Handles the OpenID Connect (OIDC) login flow.
    """
    tool_conf = DjangoToolConf(ToolConsumer)
    try:
        oidc_login = DjangoOIDCLogin(request, tool_conf)
        launch_url = get_launch_url(request)
        return oidc_login.redirect(launch_url)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def get_launch_url(request) -> str:
    """
    Constructs the LTI launch URL to which the OIDC login flow will redirect.
    """
    launch_url = request.build_absolute_uri(reverse("lti_launch"))
    return launch_url


def lti_launch(request):
    """
    Handles the LTI launch request after successful OIDC login.
    """
    tool_conf = DjangoToolConf(ToolConsumer)
    try:
        # Validate the LTI launch request
        launch = MessageLaunch(request, tool_conf)
        launch_data = launch.set_auto_validation(enable=False).validate()

        print(launch_data, "example launch data here")

        # Example: You can store or process payload data here
        return JsonResponse(
            {"message": "LTI Launch Successful", "payload": "sample payload"}
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
