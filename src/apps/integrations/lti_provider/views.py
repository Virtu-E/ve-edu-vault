"""
lti_provider.views
~~~~~~~~~~~

Main view for lti feature
"""

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from decouple import config
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from pylti1p3.contrib.django import (
    DjangoDbToolConf,
    DjangoMessageLaunch,
    DjangoOIDCLogin,
)

from course_ware.models import LearningObjective
from src.edu_vault.settings import common

tool_conf_2 = DjangoDbToolConf()


@csrf_exempt
def lti_login(request):
    """Handles the OpenID Connect (OIDC) login flow."""
    try:
        oidc_login = DjangoOIDCLogin(request, tool_conf_2)
        return oidc_login.redirect(getattr(common, "LTI_LAUNCH_URL", ""))
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def lti_launch(request):
    """Handles the LTI launch request after successful OIDC login."""
    try:
        # Validate the LTI launch request
        launch = DjangoMessageLaunch(request, tool_conf_2)

        launch_data = launch.get_launch_data()

        resource_link = launch_data[
            "https://purl.imsglobal.org/spec/lti/claim/resource_link"
        ]
        claim_context = launch_data["https://purl.imsglobal.org/spec/lti/claim/context"]
        course_id = claim_context.get("id", "")
        objective = get_object_or_404(
            LearningObjective, block_id=resource_link.get("id", "")
        )
        return redirect(
            f"{config('FRONT_END_URL')}/assessment/{course_id}/{objective.block_id}/"
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def load_public_key():
    """
    Load the public key from the PEM file.
    """
    with open("lti_provider/public_key.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())
    return public_key


def generate_kid(public_key: RSAPublicKey) -> str:
    """
    Generate a Key ID (kid) based on the public key.
    """
    # Serialize the public key to DER format
    der_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    # Compute the SHA-256 hash of the serialized key
    digest = hashes.Hash(hashes.SHA256())
    digest.update(der_public_key)
    hashed_key = digest.finalize()
    # Encode the hash in URL-safe base64 format without padding
    kid = base64.urlsafe_b64encode(hashed_key).decode("utf-8").rstrip("=")
    return kid


# TODO : dont make it hard coded -- Might deprecate it in future as well
def jwks_view(request):
    """
    Expose the public key in JWKS format.
    """
    public_key = load_public_key()
    public_numbers = public_key.public_numbers()

    # Base64 encode the modulus and exponent
    n = (
        base64.urlsafe_b64encode(
            public_numbers.n.to_bytes(
                (public_numbers.n.bit_length() + 7) // 8, byteorder="big"
            )
        )
        .decode("utf-8")
        .rstrip("=")
    )
    e = (
        base64.urlsafe_b64encode(
            public_numbers.e.to_bytes(
                (public_numbers.e.bit_length() + 7) // 8, byteorder="big"
            )
        )
        .decode("utf-8")
        .rstrip("=")
    )

    # Generate the dynamic Key ID
    kid = generate_kid(public_key)

    # Construct the JWK (JSON Web Key)
    jwk = {}
    jwks = {"keys": [jwk]}

    # Return the JWKS as a JSON response
    return JsonResponse(jwks)
