from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from pylti1p3.contrib.django import (
    DjangoDbToolConf,
    DjangoMessageLaunch,
    DjangoOIDCLogin,
)

from src.apps.integrations.lti_provider.service import get_lti_redirect_context
from src.edu_vault.settings import common

tool_conf_2 = DjangoDbToolConf()

FRONT_END_URL = getattr(common, "FRONT_END_URL")


@csrf_exempt
def lti_login(request):
    """Handles the OpenID Connect (OIDC) login flow."""
    try:
        oidc_login = DjangoOIDCLogin(request, tool_conf_2)
        return oidc_login.redirect(getattr(common, "LTI_LAUNCH_URL", ""))
    # TODO : we should catch the actual exception here instead of overall exception
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def lti_launch(request):
    """Handles the LTI launch request after successful OIDC login."""
    try:
        # Validate the LTI launch request
        launch = DjangoMessageLaunch(request, tool_conf_2)

        launch_data = launch.get_launch_data()
        return_context = get_lti_redirect_context(lti_launch_data=launch_data)

        return redirect(
            f"{FRONT_END_URL}/assessment/{return_context.course_id}/{return_context.block_id}/"
        )

    # TODO : we should catch the actual exception here instead of overall exception
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
