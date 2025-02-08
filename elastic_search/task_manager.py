import logging
from functools import lru_cache
from typing import Type

from elasticsearch import Elasticsearch

from elastic_search.api import ElasticFetch
from elastic_search.operations import ElasticsearchOperations
from elastic_search.sync import ElasticSearchSync
from elastic_search.transformer import ElasticTransformer

log = logging.getLogger(__name__)


class ElasticClientError(Exception):
    """Custom exception for Elasticsearch client errors"""

    pass


@lru_cache()
def get_elasticsearch_client() -> Elasticsearch:
    """
    Creates and returns a singleton Elasticsearch client instance.
    Uses environment variables for configuration.

    Returns:
        Elasticsearch: Configured Elasticsearch client

    Raises:
        ElasticClientError: If connection cannot be established
    """
    # TODO : make dynamic configuration
    # es_host = config('ES_HOST', default='localhost')
    # es_port = config('ES_PORT', default='9200')
    # es_api_key = config('ES_API_KEY', default=None)

    client = Elasticsearch(
        ["https://d81dc60cb8b440b689c376163dfb471a.us-central1.gcp.cloud.es.io:443"],
        api_key="YXZmaTVwUUJJTnJBNWlRcEY3bHA6dmozMFlXV3RTMzY3WjdaaGdqa0xpUQ==",
    )

    if not client.ping():
        raise ElasticClientError("Failed to connect to Elasticsearch")

    return client


class ElasticTaskManager:
    """Manages Elasticsearch related tasks"""

    def __init__(
        self, handler: Type[ElasticsearchOperations], index_name: str = "topics"
    ):
        self._client = get_elasticsearch_client()
        self._index_name = index_name
        self._handler = handler(self._client, self._index_name)

    def _log_es_info(self):
        """Logs Elasticsearch version information"""
        try:
            es_info = self._client.info()
            log.info(
                f"Connected to Elasticsearch version: {es_info['version']['number']}"
            )
        except Exception as e:
            log.error(f"Failed to fetch Elasticsearch info: {str(e)}")

    def sync_course(self, course_id: str) -> None:
        """
        Synchronizes course data with Elasticsearch

        Args:
            course_id: ID of the course to sync
        """
        try:
            self._log_es_info()

            fetcher = ElasticFetch(course_id)
            transformer = ElasticTransformer()

            ElasticSearchSync(
                data_fetcher=fetcher,
                data_transformer=transformer,
                es_handler=self._handler,
            ).sync_data()

        except Exception as e:
            log.error(f"Failed to sync course {course_id}: {str(e)}")
            raise

    def delete_index(self, index_id: str) -> None:
        """
        Deletes an index from Elasticsearch

        Args:
            index_id: ID of the index to delete
        """
        try:
            self._handler.delete(topic_id=index_id)
        except Exception as e:
            log.error(f"Failed to delete index {index_id}: {str(e)}")
            raise
