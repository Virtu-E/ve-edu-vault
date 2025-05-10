"""
oauth_clients.edx_client
~~~~~~~~~

Edx OAuth client for calling Edx related APIs.
"""

import logging
from typing import Any, Dict, Optional

from decouple import config

from src.apps.integrations.oauth_clients.services import (
    OAuthClient,
    get_edx_oauth_client,
)

log = logging.getLogger(__name__)


# TODO : thinking of making this a singleton class instance
# TODO : catch error responses that can happen, and make necessary moves
class EdxClient:
    def __init__(self, client: OAuthClient):
        self.client = client
        self.studio_url = config("EDX_STUDIO_URL")
        self.lms_url = config("EDX_LMS_URL")

    async def make_request(self, method: str, url: str, params: Optional[Dict] = None):
        """Helper method to make a request."""
        return await self.client.make_request(method, url, params=params)

    async def get_course_outline(self, course_id: str) -> Optional[Dict]:
        """Fetch course outline from OpenEdX API."""
        url = f"{self.studio_url}/api/contentstore/v1/course_index/{course_id}"
        response = await self.make_request("GET", url)
        return response

    async def get_course_blocks(self, block_id: str) -> Optional[Dict]:
        """Fetch course blocks from OpenEdX API."""
        url = f"{self.lms_url}/api/courses/v1/blocks/{block_id}"
        params = {"depth": "all", "all_blocks": "true"}
        response = await self.make_request("GET", url, params=params)
        return response

    # TODO : i need to add a proper data type return here
    async def get_public_course_outline(self, course_id: str) -> Any:
        """Fetch public course outline from OpenEdX API."""
        url = f"{self.lms_url}/api/course_home/outline/{course_id}"
        response = await self.make_request("GET", url)
        return response


async def get_edx_client() -> EdxClient:
    oauth_client = await get_edx_oauth_client()
    return EdxClient(oauth_client)
