from typing import Dict

from decouple import config

from oauth_clients.services import OAuthClient

edx_client = OAuthClient(service_type="OPENEDX")
EDX_STUDIO_URL = config("EDX_STUDIO_URL")
EDX_LMS_URL = config("EDX_LMS_URL")


# TODO : add efficient error handling scenarios here, to prevent system glitch if error
def get_course_outline(course_id: str) -> Dict | None:
    """Fetch course outline from OpenEdX API."""
    url = f"{EDX_STUDIO_URL}/api/contentstore/v1/course_index/{course_id}"
    response = edx_client.make_request("GET", url)
    if response.status_code == 200:
        return response.json()
    return None


def get_course_blocks(block_id: str) -> Dict | None:
    """Fetch course blocks from OpenEdX API."""
    url = f"{EDX_LMS_URL}/api/courses/v1/blocks/{block_id}"
    params = {"depth": "all", "all_blocks": "true"}
    response = edx_client.make_request("GET", url, params=params)
    if response.status_code == 200:
        return response.json()
    return None
