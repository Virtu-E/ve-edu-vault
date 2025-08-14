import pytest
from knox.models import AuthToken
from rest_framework.test import APIClient

from src.apps.core.users.models import EdxUser


@pytest.fixture(autouse=True)
def enable_db_access(db):
    """Automatically enable database access for all tests"""
    return


@pytest.fixture
def default_edx_user():
    return EdxUser.objects.create(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="",
        active=True,
    )


@pytest.fixture
def authenticated_client(default_edx_user):
    client = APIClient()
    token_instance, token = AuthToken.objects.create(default_edx_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    return client


@pytest.fixture
def unauthenticated_client():
    return APIClient()


@pytest.fixture
def invalid_token_client():
    """Create a client with invalid token"""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token invalid_token_here")
    return client
