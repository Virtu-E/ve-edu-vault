# lti_provider/views.py


import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.http import JsonResponse
from django.shortcuts import redirect
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
        return oidc_login.redirect("https://vault.virtueducate.edly.io/lti/launch/")
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
        return redirect(
            "https://virtueducate.edly.io/assesment/block-v1:VirtuEducate+100+2024+type@lti_consumer+block@e8fdb7a5189d4802a4c4ae8de231425d"
        )

    except Exception as e:
        print(e, " here is an error message")
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


# TODO : dont make it hard coded
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
    jwk = {
        "e": e,
        "kid": kid,
        "kty": "RSA",
        "n": n,
        "alg": "RS256",
        "use": "sig",
    }

    # Wrap the JWK in a JSON Web Key Set (JWKS)
    jwks = {"keys": [jwk]}

    # Return the JWKS as a JSON response
    return JsonResponse(jwks)
