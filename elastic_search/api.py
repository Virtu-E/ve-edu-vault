from abc import ABC, abstractmethod
from typing import Any

from oauth_clients.edx_client import EdxClient


class DataFetcher(ABC):
    # TODO : i need to add a proper data type return here
    @abstractmethod
    def fetch_data(self) -> Any:
        pass


class ElasticFetch(DataFetcher):
    def __init__(self, course_id: str):
        self._client = EdxClient("OPENEDX")
        self._course_id = course_id

    def fetch_data(self) -> Any:
        try:
            return self._client.get_public_course_outline(self._course_id)
        except Exception as e:
            raise Exception(f"Failed to fetch data: {str(e)}")
