from abc import ABC, abstractmethod
from typing import Any

import certifi
from pymongo import MongoClient

from exceptions import MongoDbConfigurationError


class NoSqLDatabaseEngineInterface(ABC):
    @abstractmethod
    def fetch_from_db(self, collection_name: str, database_name: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def write_to_db(self, data: Any, collection_name: str, database_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError


class MongoDatabaseEngine(NoSqLDatabaseEngineInterface):
    """Mongo database engine implementation."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
        return cls._instance

    def __init__(self, mongo_url: str | None = None) -> None:
        """Avoid re-initialization for the singleton instance"""
        if hasattr(self, "_initialized") and self._initialized:
            return

        if mongo_url is None:
            raise MongoDbConfigurationError("MongoDB connection URL is required")

        self._url = mongo_url
        self._client = MongoClient(self._url, tlsCAFile=certifi.where())
        self._initialized = True  # Mark instance as initialized

    def fetch_from_db(self, collection_name: str, database_name: str) -> Any:
        db = self._client.get_database(database_name)
        collection = db.get_collection(collection_name)
        return collection

    def write_to_db(self, data: Any, collection_name: str, database_name: str) -> None:
        db = self._client.get_database(database_name)
        collection = db.get_collection(collection_name)
        collection.insert_one(data)

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
