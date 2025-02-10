import logging
from typing import Any, Dict, Optional

from decouple import config

from oauth_clients.services import OAuthClient

log = logging.getLogger(__name__)


# TODO : thinking of making this a singleton class instance
class EdxClient:
    def __init__(self, service_type=""):
        self.client = OAuthClient(service_type=service_type)
        self.studio_url = config("EDX_STUDIO_URL")
        self.lms_url = config("EDX_LMS_URL")

    def make_request(self, method: str, url: str, params: Optional[Dict] = None):
        """Helper method to make a request."""
        try:
            return self.client.make_request(method, url, params=params)
        except Exception as e:
            print(f"Error making {method} request to {url}: {e}")
            return None

    def get_course_outline(self, course_id: str) -> Optional[Dict]:
        """Fetch course outline from OpenEdX API."""
        url = f"{self.studio_url}/api/contentstore/v1/course_index/{course_id}"
        response = self.make_request("GET", url)
        if response and response.status_code == 200:
            return response.json()
        return None

    def get_course_blocks(self, block_id: str) -> Optional[Dict]:
        """Fetch course blocks from OpenEdX API."""
        url = f"{self.lms_url}/api/courses/v1/blocks/{block_id}"
        params = {"depth": "all", "all_blocks": "true"}
        response = self.make_request("GET", url, params=params)
        if response and response.status_code == 200:
            return response.json()
        return None

    # TODO : i need to add a proper data type return here
    def get_public_course_outline(self, course_id: str) -> Any:
        """Fetch public course outline from OpenEdX API."""
        url = f"{self.lms_url}/api/course_home/outline/{course_id}"
        response = self.make_request("GET", url)
        if response and response.status_code == 200:
            return response.json()
        log.error(f"Error fetching course outline for {course_id}: {response}")
        return None
