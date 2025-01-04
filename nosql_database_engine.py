import logging
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional, Union

import certifi
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

from exceptions import (
    MongoDbConfigurationError,
    MongoDbConnectionError,
    MongoDbOperationError,
)

log = logging.getLogger(__name__)


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
    """
    MongoDB database engine implementation using the Singleton pattern.

    This class provides a thread-safe interface to MongoDB operations with proper
    connection management, error handling, and logging.

    Attributes:
        _instance: Singleton instance of the class
        _url: MongoDB connection URL
        _client: PyMongo client instance
        _initialized: Flag to track initialization status
        logger: Class logger instance
    """

    _instance: Optional["MongoDatabaseEngine"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "MongoDatabaseEngine":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                cls._instance = instance
            return cls._instance

    def __init__(self, mongo_url: Optional[str] = None) -> None:
        """
        Initialize the MongoDB engine.

        Args:
            mongo_url: MongoDB connection URL. Required for first initialization.

        Raises:
            MongoDbConfigurationError: If mongo_url is missing during first initialization.
        """
        with self._lock:
            if hasattr(self, "_initialized") and self._initialized:
                return

            self.logger = log

            if mongo_url is None:
                raise MongoDbConfigurationError("MongoDB connection URL is required")

            self._url = mongo_url
            self._client = None
            self._initialized = True
            self._connect()

    def _connect(self) -> None:
        """
        Establish connection to MongoDB.

        Raises:
            MongoDbConnectionError: If connection fails.
        """
        try:
            self._client = MongoClient(
                self._url,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,  # 5 second timeout
            )
            # Verify connection
            self._client.server_info()
            self.logger.info("Successfully connected to MongoDB")
        except (ConnectionError, ServerSelectionTimeoutError) as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise MongoDbConnectionError(f"Could not connect to MongoDB: {str(e)}")

    @contextmanager
    def get_collection(self, collection_name: str, database_name: str) -> Collection:
        """
        Get a MongoDB collection with automatic connection management.

        Args:
            collection_name: Name of the collection
            database_name: Name of the database

        Yields:
            pymongo.collection.Collection: MongoDB collection object

        Raises:
            MongoDbConnectionError: If connection is lost or invalid
            MongoDbOperationError: If collection/database access fails
        """
        if not self._client:
            self._connect()

        try:
            db: Database = self._client.get_database(database_name)
            collection: Collection = db.get_collection(collection_name)
            yield collection
        except OperationFailure as e:
            self.logger.error(
                f"Failed to access collection {collection_name}: {str(e)}"
            )
            raise MongoDbOperationError(f"Collection operation failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error accessing collection: {str(e)}")
            raise

    def fetch_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict = None,
        projection: Dict = None,
    ) -> list:
        """
        Fetch documents from MongoDB collection.

        Args:
            collection_name: Name of the collection
            database_name: Name of the database
            query: MongoDB query filter
            projection: Fields to include/exclude in the result

        Returns:
            list: List of documents matching the query

        Raises:
            MongoDbOperationError: If the fetch operation fails
        """
        query = query or {}
        projection = projection or {}

        try:
            with self.get_collection(collection_name, database_name) as collection:
                return list(collection.find(query, projection))
        except Exception as e:
            self.logger.error(f"Error fetching from {collection_name}: {str(e)}")
            raise MongoDbOperationError(f"Failed to fetch data: {str(e)}")

    def write_to_db(
        self,
        data: Union[Dict, list],
        collection_name: str,
        database_name: str,
        timestamp: bool = True,
    ) -> None:
        """
        Write data to MongoDB collection.

        Args:
            data: Document or list of documents to insert
            collection_name: Name of the collection
            database_name: Name of the database
            timestamp: Whether to add timestamp to documents

        Raises:
            MongoDbOperationError: If the write operation fails
        """
        try:
            with self.get_collection(collection_name, database_name) as collection:
                if isinstance(data, list):
                    if timestamp:
                        for doc in data:
                            doc["created_at"] = datetime.utcnow()
                    collection.insert_many(data)
                else:
                    if timestamp:
                        data["created_at"] = datetime.utcnow()
                    collection.insert_one(data)
                self.logger.debug(f"Successfully wrote data to {collection_name}")
        except Exception as e:
            self.logger.error(f"Error writing to {collection_name}: {str(e)}")
            raise MongoDbOperationError(f"Failed to write data: {str(e)}")

    def disconnect(self) -> None:
        """
        Safely close MongoDB connection.
        """
        if self._client:
            try:
                self._client.close()
                self.logger.info("Disconnected from MongoDB")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {str(e)}")
            finally:
                self._client = None

    def __del__(self) -> None:
        """
        Ensure connection is closed when object is destroyed.
        """
        self.disconnect()
