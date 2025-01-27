import requests
from django.core.cache import cache

from .models import OAuthClientConfig


class OAuthClient:
    def __init__(self, service_type=None, config_name=None):
        if config_name:
            self.config = OAuthClientConfig.objects.get(name=config_name)
        elif service_type:
            self.config = OAuthClientConfig.objects.get(
                service_type=service_type, is_active=True
            )
        else:
            raise ValueError("Either service_type or config_name must be provided")

        self.base_url = self.config.base_url
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        self.service_type = self.config.service_type

    def _get_cache_key(self):
        return f"oauth_token_{self.config.name}"

    def _get_token_url(self):
        """Get token URL based on service type."""
        if self.service_type == "OPENEDX":
            return f"{self.base_url}/oauth2/access_token"
        # Add other service types token URLs here
        return f"{self.base_url}/oauth/token"  # default

    def get_access_token(self):
        """Get a new access token from the service."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        # Add service-specific token requirements
        if self.service_type == "OPENEDX":
            data["token_type"] = "jwt"

        response = requests.post(self._get_token_url(), data=data)
        response.raise_for_status()
        return response.json()

    def get_valid_token(self):
        """Get a valid token from cache or request a new one."""
        cache_key = self._get_cache_key()
        token = cache.get(cache_key)

        if not token:
            token_data = self.get_access_token()
            token = token_data["access_token"]
            # Cache the token with a safety margin
            cache_duration = token_data.get("expires_in", 3600) - 300
            cache.set(cache_key, token, cache_duration)

        return token

    def make_request(self, method, endpoint, **kwargs):
        """Make an authenticated request to the service."""
        headers = kwargs.pop("headers", {})

        # Add service-specific auth header format
        if self.service_type == "OPENEDX":
            headers["Authorization"] = f"JWT {self.get_valid_token()}"
        else:
            headers["Authorization"] = f"Bearer {self.get_valid_token()}"

        url = f"{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response
