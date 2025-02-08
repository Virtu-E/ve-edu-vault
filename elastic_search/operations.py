import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from elasticsearch import Elasticsearch

from data_types.elastic_search import TopicData

log = logging.getLogger(__name__)


class ElasticsearchOperations(ABC):

    def __init__(self, es_client: Elasticsearch, index_name: str) -> None:
        self._es = es_client
        self._index_name = index_name

    @abstractmethod
    def create_or_update(self, data: TopicData) -> bool:
        pass

    @abstractmethod
    def delete(self, topic_id: str) -> bool:
        pass

    @abstractmethod
    def bulk_update(self, data: List[TopicData]) -> Dict[str, int]:
        pass


class Sync(ABC):
    @abstractmethod
    def sync_data(self) -> Dict[str, Any]:
        pass


class ElasticSearchHandler(ElasticsearchOperations):
    def __init__(self, es_client: Elasticsearch, index_name: str):
        super().__init__(es_client, index_name)
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        try:
            if not self._es.indices.exists(index=self._index_name):
                mappings = {
                    "mappings": {
                        "properties": {
                            "topic_name": {"type": "text"},
                            "topic_id": {"type": "keyword"},
                            "course_id": {"type": "keyword"},
                            "course_name": {"type": "text"},
                            "learning_objectives": {
                                "type": "nested",
                                "properties": {
                                    "name": {"type": "text"},
                                    "id": {"type": "keyword"},
                                },
                            },
                            "metadata": {
                                "properties": {
                                    "created_at": {"type": "date"},
                                    "updated_at": {"type": "date"},
                                }
                            },
                        }
                    },
                    "settings": {"number_of_shards": 1, "number_of_replicas": 1},
                }

                self._es.indices.create(
                    index=self._index_name,
                    mappings=mappings["mappings"],
                    settings=mappings["settings"],
                )
        except Exception as e:
            raise Exception(f"Failed to create index: {str(e)}")

    def create_or_update(self, data: TopicData) -> bool:
        try:
            self._es.index(
                index=self._index_name, id=data.topic_id, document=self._to_dict(data)
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to create/update document: {str(e)}")

    def delete(self, topic_id: str) -> bool:
        try:
            self._es.delete(index=self._index_name, id=topic_id)
            return True
        except Exception as e:
            log.error(f"Failed to delete document: {str(e)}")

    def bulk_update(self, data: List[TopicData]) -> Dict[str, int]:
        operations = []
        for item in data:
            # Convert LearningObjective objects to dictionaries
            learning_objectives = [
                {"name": obj.name, "id": obj.id} for obj in item.learning_objectives
            ]

            doc = self._to_dict(item)
            doc["learning_objectives"] = learning_objectives

            operations.extend(
                [{"index": {"_index": self._index_name, "_id": item.topic_id}}, doc]
            )

        if operations:
            try:
                # Use the correct keyword argument 'operations' instead of positional
                response = self._es.bulk(operations=operations)
                return {
                    "total": len(data),
                    "succeeded": sum(
                        1
                        for item in response["items"]
                        if "index" in item and item["index"]["status"] < 300
                    ),
                    "failed": sum(
                        1
                        for item in response["items"]
                        if "index" in item and item["index"]["status"] >= 300
                    ),
                }
            except Exception as e:
                raise Exception(f"Failed to perform bulk update: {str(e)}")
        return {"total": 0, "succeeded": 0, "failed": 0}

    def _to_dict(self, data: TopicData) -> Dict[str, Any]:
        return {
            "topic_id": data.topic_id,
            "topic_name": data.topic_name,
            "course_id": data.course_id,
            "course_name": data.course_name,
            "learning_objectives": data.learning_objectives,
        }
