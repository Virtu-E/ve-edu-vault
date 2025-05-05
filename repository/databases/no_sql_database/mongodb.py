"""
repository.databases.no_sql_database.mongodb
~~~~~~~~~~~

Implementation for MongoDB using motor (AsyncMongoClient) which
exposes the database using python module singleton pattern
"""

import asyncio
import gc
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import certifi
import pymongo.errors
from django.conf import settings
from motor.motor_asyncio import AsyncIOMotorClient

from .exceptions import (
    MongoDbConfigurationError,
    MongoDbConnectionError,
    MongoDbOperationError,
)
from .nosql_database_engine import AsyncBaseNoSqLDatabaseEngine

log = logging.getLogger(__name__)


class AsyncMongoDatabaseEngine(AsyncBaseNoSqLDatabaseEngine):
    """
    Asynchronous MongoDB database engine implementation

    This class provides an async interface to MongoDB operations with proper
    connection management, error handling, and connection pooling.
    """

    def __init__(self, mongo_url: Optional[str] = None) -> None:
        """
        Initialize the Async MongoDB engine.

        Args:
            mongo_url: MongoDB connection URL. Required for initialization.

        Raises:
            MongoDbConfigurationError: If mongo_url is missing during initialization.
        """
        self._logger = log

        if mongo_url is None:
            raise MongoDbConfigurationError("MongoDB connection URL is required")

        self._url = mongo_url
        self._client: AsyncIOMotorClient | None = None
        self._connection_lock = asyncio.Lock()

    async def _get_client(self) -> AsyncIOMotorClient:
        """
        Get or create a MongoDB client with connection pooling.

        Returns:
            AsyncIOMotorClient: MongoDB async client

        Raises:
            MongoDbConnectionError: If connection fails
        """
        async with self._connection_lock:
            if self._client is None:
                try:
                    # Create client with connection pooling configuration
                    # TODO : make this configurable in settings
                    self._client = AsyncIOMotorClient(
                        self._url,
                        tlsCAFile=certifi.where(),
                        serverSelectionTimeoutMS=5000,  # Reduced from 10000
                        maxPoolSize=10,  # Reduced from 100
                        minPoolSize=0,  # Reduced from 10
                        waitQueueTimeoutMS=1000,  # Reduced from 2500
                        retryWrites=True,
                        connectTimeoutMS=2000,  # Reduced from 5000
                        socketTimeoutMS=5000,  # Reduced from 10000
                    )
                    await self._client.admin.command("ping")
                    self._logger.info("Successfully connected to MongoDB")
                except Exception as e:
                    self._logger.error("Failed to connect to MongoDB: %s", e)
                    raise MongoDbConnectionError(
                        message=f"Could not connect to MongoDB: {str(e)}",
                        details=str(e),
                        operation="connect",
                    ) from e

            return self._client

    async def _get_collection(self, collection_name: str, database_name: str):
        """
        Get a MongoDB collection with automatic connection management.

        Args:
            collection_name (str): Name of the collection
            database_name (str): Name of the database

        Returns:
            AsyncIOMotorCollection: MongoDB collection object

        Raises:
            MongoDbConnectionError: If connection is lost or invalid
        """
        client = await self._get_client()
        db = client[database_name]
        collection = db[collection_name]
        return collection

    async def fetch_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict | None = None,
        projection: Dict | None = None,
        batch_size: int = 10,
        limit: int = 10,
        skip: int = 0,
        sort: List[tuple] | None = None,
    ) -> AsyncGenerator[List[Dict], None]:
        """
        Fetch documents from MongoDB collection asynchronously in batches.

        Args:
            collection_name: Name of the collection
            database_name: Name of the database
            query: MongoDB query filter
            projection: Fields to include/exclude in the result
            batch_size: Number of documents to fetch in each batch
            limit: Maximum number of documents to fetch (0 for no limit)
            skip: Number of documents to skip
            sort: Fields to sort by

        Returns:
            AsyncGenerator[List[Dict], None]: A coroutine that returns a generator yielding batches of documents

        Raises:
            MongoDbOperationError: If the fetch operation fails
        """

        async def generator() -> AsyncGenerator[List[Dict], None]:
            query_dict = query or {}
            projection_dict = projection or {}
            total_fetched = 0

            try:
                collection = await self._get_collection(collection_name, database_name)
                cursor = collection.find(query_dict, projection_dict)
                if skip > 0:
                    cursor = cursor.skip(skip)
                if sort:
                    cursor = cursor.sort(sort)

                try:
                    while True:
                        # Calculate how many documents to fetch in this batch
                        current_batch_size = batch_size
                        if limit > 0:
                            remaining = limit - total_fetched
                            if remaining <= 0:
                                break
                            current_batch_size = min(batch_size, remaining)

                        # Fetch a batch
                        batch = await cursor.to_list(length=current_batch_size)
                        if not batch:
                            break

                        yield batch

                        total_fetched += len(batch)
                        if limit > 0 and total_fetched >= limit:
                            break
                finally:
                    await cursor.close()

            except Exception as e:
                self._logger.error("Error fetching from %s: %s", collection_name, e)
                raise MongoDbOperationError(
                    message=f"Failed to fetch data: {str(e)}",
                    operation="fetch",
                    collection=collection_name,
                    query=query_dict,
                    details=str(e),
                ) from e

        return generator()  # Return the generator

    async def fetch_one_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict | None = None,
        projection: Dict | None = None,
    ) -> Optional[Dict | List]:
        """
        Fetch a single document from MongoDB collection asynchronously.

        Args:
            collection_name: Name of the collection
            database_name: Name of the database
            query: MongoDB query filter
            projection: Fields to include/exclude in the result

        Returns:
            Dict: Single document matching the query or None if no match found

        Raises:
            MongoDbOperationError: If the fetch operation fails
        """
        query = query or {}
        projection = projection or {}

        try:
            collection = await self._get_collection(collection_name, database_name)
            result = await collection.find_one(query, projection)
            return result
        except Exception as e:
            self._logger.error("Error fetching one from %s: %s", collection_name, e)
            raise MongoDbOperationError(
                message=f"Failed to fetch single document: {str(e)}",
                operation="fetch_one",
                collection=collection_name,
                query=query,
                details=str(e),
            ) from e

    async def write_to_db(
        self,
        data: Union[Dict, list],
        collection_name: str,
        database_name: str,
        timestamp: bool = True,
    ) -> None:
        """
        Write data to MongoDB collection asynchronously.

        Args:
            data: Document or list of documents to insert
            collection_name: Name of the collection
            database_name: Name of the database
            timestamp: Whether to add timestamp to documents

        Raises:
            MongoDbOperationError: If the write operation fails
        """
        try:
            collection = await self._get_collection(collection_name, database_name)

            if isinstance(data, list):
                if timestamp:
                    data = [
                        {**doc, "created_at": datetime.now(timezone.utc)}
                        for doc in data
                    ]
                await collection.insert_many(data)
                return

            if timestamp:
                data["created_at"] = datetime.now(timezone.utc)
            await collection.insert_one(data)

        except Exception as e:
            self._logger.error("Error writing to %s: %s", collection_name, e)
            raise MongoDbOperationError(
                message=f"Failed to write data: {str(e)}",
                operation="write",
                collection=collection_name,
                details=str(e),
            ) from e
        finally:
            self._logger.debug("Successfully wrote data to %s", collection_name)

    async def run_aggregation(
        self,
        collection_name: str,
        database_name: str,
        pipeline: List[Any],
    ) -> List[Dict[str, List[Any]]]:
        """
        Execute an aggregation pipeline on a MongoDB collection asynchronously.

        Args:
            collection_name: Name of the collection
            database_name: Name of the database
            pipeline: Aggregation pipeline as a list of stages

        Returns:
            list: List of documents resulting from the aggregation pipeline

        Raises:
            MongoDbOperationError: If the aggregation operation fails
        """
        try:
            collection = await self._get_collection(collection_name, database_name)
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)  # Fetch all results

            self._logger.info(
                "Successfully executed aggregation pipeline. "
                "Aggregation query executed on %s: %s",
                collection_name,
                pipeline,
            )
            return results
        # TODO : dont catch generic exceptions
        except Exception as e:
            self._logger.error(
                "Error running aggregation on %s: %s", collection_name, e
            )
            raise MongoDbOperationError(
                message=f"Failed to execute aggregation: {str(e)}",
                operation="aggregation",
                collection=collection_name,
                query=pipeline,
                details=str(e),
            ) from e

    # TODO : make sure this is called when the SIGTERM or django shutdown process
    async def disconnect(self) -> None:
        """
        Safely close MongoDB connection asynchronously.
        """
        if self._client:
            try:
                self._client.close()
                self._logger.info("Disconnected from MongoDB")
            except pymongo.errors.NetworkTimeout as e:
                self._logger.error("Timeout during MongoDB disconnect: %s", e)
            except pymongo.errors.ConnectionFailure as e:
                self._logger.error(
                    "Connection failure during MongoDB disconnect: %s", e
                )
            except pymongo.errors.PyMongoError as e:
                self._logger.error("PyMongo error during MongoDB disconnect: %s", e)
            except Exception as e:
                self._logger.error("Unexpected error during MongoDB disconnect: %s", e)

            finally:
                self._client = None

        # Ensure client reference is cleared and initiate garbage collection if needed
        if self._client is not None:
            self._logger.warning(
                "MongoDB connection might still be active. "
                "Initiating python garbage collection manually"
            )
            self._client = None
            gc.collect()


mongo_database = AsyncMongoDatabaseEngine(getattr(settings, "MONGO_URL", None))
