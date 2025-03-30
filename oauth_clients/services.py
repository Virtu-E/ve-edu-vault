"""
oauth_clients.services
~~~~~~~~~~~~~

Includes OauthClient Service
"""

import aiohttp
from django.core.cache import cache

from .models import OAuthClientConfig


class OAuthClient:
    def __init__(self, service_type=None, config_name=None):
        self._config = self.get_config(config_name, service_type)
        self._base_url = self._config.base_url
        self._client_id = self._config.client_id
        self._client_secret = self._config.client_secret
        self._service_type = self._config.service_type
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()

    @staticmethod
    def get_config(config_name=None, service_type=None):
        if config_name:
            return OAuthClientConfig.objects.get(name=config_name)
        elif service_type:
            return OAuthClientConfig.objects.get(
                service_type=service_type, is_active=True
            )
        else:
            raise ValueError("Either service_type or config_name must be provided")

    def _get_cache_key(self):
        return f"oauth_token_{self._config.name}"

    def _get_token_url(self):
        """Get token URL based on service type."""
        if self._service_type == "OPENEDX":
            return f"{self._base_url}/oauth2/access_token"
        # Add other service types token URLs here
        return f"{self._base_url}/oauth/token"  # default

    async def get_access_token(self):
        """Get a new access token from the service asynchronously."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        # Add service-specific token requirements
        if self._service_type == "OPENEDX":
            data["token_type"] = "jwt"

        async with self._session.post(self._get_token_url(), data=data) as response:
            response.raise_for_status()
            return await response.json()

    async def get_valid_token(self):
        """Get a valid token from cache or request a new one asynchronously."""
        cache_key = self._get_cache_key()
        token = cache.get(cache_key)

        if not token:
            token_data = await self.get_access_token()
            token = token_data["access_token"]
            # Cache the token with a safety margin
            cache_duration = token_data.get("expires_in", 3600) - 300
            cache.set(cache_key, token, cache_duration)

        return token

    async def make_request(self, method, endpoint, **kwargs):
        """Make an authenticated request to the service asynchronously."""
        headers = kwargs.pop("headers", {}) if "headers" in kwargs else {}

        # Add service-specific auth header format
        if self._service_type == "OPENEDX":
            headers["Authorization"] = f"JWT {await self.get_valid_token()}"
        else:
            headers["Authorization"] = f"Bearer {await self.get_valid_token()}"

        async with self._session.request(
            method, endpoint, headers=headers, **kwargs
        ) as response:
            # Not raising error immediately to allow caller to handle specific status codes
            return response
