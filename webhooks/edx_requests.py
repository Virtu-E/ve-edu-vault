from oauth_clients.services import OAuthClient


def get_course_outline(course_id: str) -> dict:
    try:
        client = OAuthClient(service_type="OPENEDX")
        response = client.make_request(
            "GET",
            f"https://studio.local.edly.io/api/contentstore/v1/course_index/{course_id}",
        )
        return response.json()
    except Exception as e:
        raise e
