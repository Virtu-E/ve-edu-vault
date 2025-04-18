"""
oauth_clients.services
~~~~~~~~~~~~~

Includes OauthClient Service
"""

import ssl

import aiohttp
from asgiref.sync import sync_to_async
from django.core.cache import cache

from .models import OAuthClientConfig


class OAuthClient:
    def __init__(self, service_type=None, config_name=None):
        self.service_type = service_type
        self.config_name = config_name
        self._config = None
        self._base_url = None
        self._client_id = None
        self._client_secret = None
        self._service_type = None
        self._session = None

    async def __aenter__(self):
        await self._setup_data()

        # TODO : SSL -> enable for production
        # Create an SSL context that does not verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create a ClientSession with the custom SSL context
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl_context=ssl_context)
        )

        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()

    async def _setup_data(self):
        config = await self.get_config(self.config_name, self.service_type)
        self._base_url = config.base_url
        self._client_id = config.client_id
        self._client_secret = config.client_secret
        self._service_type = config.service_type
        self._config = config

    @staticmethod
    async def get_config(config_name=None, service_type=None):
        if config_name:
            return await sync_to_async(OAuthClientConfig.objects.get)(name=config_name)
        elif service_type:
            return await sync_to_async(OAuthClientConfig.objects.get)(
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

            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()  # Raise an error for non-200 status codes
