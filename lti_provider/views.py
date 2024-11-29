# lti_provider/views.py

from cryptography.hazmat.primitives import serialization
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from pylti1p3.contrib.django import (
    DjangoDbToolConf,
    DjangoMessageLaunch,
    DjangoOIDCLogin,
)

tool_conf_2 = DjangoDbToolConf()


@csrf_exempt
def lti_login(request):
    """
    Handles the OpenID Connect (OIDC) login flow.
    """
    try:
        oidc_login = DjangoOIDCLogin(request, tool_conf_2)
        get_launch_url(request)
        return oidc_login.redirect("https://virtueducate.edly.io/lti/launch/")
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=400)


def get_launch_url(request) -> str:
    """
    Constructs the LTI launch URL to which the OIDC login flow will redirect.
    """
    # TODO : Need to dynamically get the target uri from the platform tool here
    launch_url = request.build_absolute_uri(reverse("lti_launch"))
    return launch_url


@csrf_exempt
def lti_launch(request):
    """
    Handles the LTI launch request after successful OIDC login.
    """
    try:
        # Validate the LTI launch request
        launch = DjangoMessageLaunch(request, tool_conf_2)

        launch_data = launch.get_launch_data()

        print(launch_data)

        # Example: You can store or process payload data here
        return JsonResponse(
            {"message": "LTI Launch Successful", "payload": "sample payload"}
        )

    except Exception as e:
        print(e, "here here is an error message")
        return JsonResponse({"error": str(e)}, status=400)


def load_public_key():
    """
    Load the public key from the PEM file.
    """
    with open("lti_provider/public_key.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())
    return public_key


# TODO : dont make it hard coded
def jwks_view(request):
    """
    Expose the public key in JWKS format.
    """
    public_key = load_public_key()
    public_key.public_numbers()

    # Construct the JWK (JSON Web Key)
    jwk = {
        "e": "AQAB",  # Public exponent
        "kid": "q2IZGBMbJQdpokvk4-yvf7G3g_AD9AUl1JU5dJWXZ-g",  # Key ID
        "kty": "RSA",  # Key type (RSA)
        # This is a very long string that exceeds the line length limit, but we are ignoring it  # noqa: E501
        "n": "yGp6gbpugPvgg3W_joITFYSqYUT6fYPvHGjZjPL_7d9wVZFM2sLRMjPkYxff4hEuEmTjwPTByKD5oYeyiqUKKZCgbZ5Jhh9hOfMaKZ0bOM2VG2wSk8ucPmxoTqEUQtxbOqj8sDwsTo7Wr6bA6fB2KjWqV32giHBVFiiPIBx0UieZRyCI8gwDhtSGJx3i9dFDrssokhBRqsPI9xlYpVulN7DLjk00SYG6w62kKuUAaabYe8cUEg0Kt8KwpUvZPSirJqwXqsX4s6GlUQ4qQ6Yt_mvFtxsElmzWJ5-zbKNJ3JO9zvtNAx1pC_lVFkC20T1YWm96Zcd-JUl0afUvnU13Fw",  # noqa: E501
        "alg": "RS256",  # Algorithm (RS256)
        "use": "sig",  # Intended use (signature)
    }

    # Wrap the JWK in a JSON Web Key Set (JWKS)
    jwks = {"keys": [jwk]}

    # Return the JWKS as a JSON response
    return JsonResponse(jwks)
