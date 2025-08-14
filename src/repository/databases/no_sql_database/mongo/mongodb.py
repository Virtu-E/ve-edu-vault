import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from urllib.parse import ParseResult, urlparse

import certifi
from django.conf import settings
from pymongo import AsyncMongoClient
from pymongo.errors import (AutoReconnect, ConfigurationError,
                            ConnectionFailure, CursorNotFound,
                            DocumentTooLarge, DuplicateKeyError,
                            ExecutionTimeout, NetworkTimeout, NotPrimaryError,
                            OperationFailure, PyMongoError,
                            ServerSelectionTimeoutError, WTimeoutError)

from src.exceptions import (MongoDbConfigurationError, MongoDbConnectionError,
                            MongoDbOperationError,
                            MongoDbTemporaryConnectionError,
                            MongoDbTemporaryOperationError)

from ..async_base_engine import AsyncAbstractNoSqLDatabaseEngine

logger = logging.getLogger(__name__)


class AsyncMongoDatabaseEngine(AsyncAbstractNoSqLDatabaseEngine):
    """
    Async MongoDB engine with connection management and error handling.
    """

    __slots__ = ("_url", "_client")

    def __init__(
        self, mongo_url: Optional[str] = None, client: Optional[AsyncMongoClient] = None
    ):
        """
        Initialize MongoDB engine.

        Args:
            mongo_url: MongoDB connection URL
            client: Optional AsyncMongoClient class for dependency injection

        Raises:
            MongoDbConfigurationError: If mongo_url is missing
        """
        if mongo_url is None:
            logger.error("MongoDB URL not provided during initialization")
            raise MongoDbConfigurationError(
                message="MongoDB connection URL is required but not provided",
                missing_config="MONGO_URL",
                config_file="config.django.base.py",
                expected_format="mongodb://username:password@host:port/database",
            )

        self._url = mongo_url
        self._client: Optional[AsyncMongoClient] = client
        logger.debug("MongoDB engine initialized with URL: %s", self.host)

    async def _get_client(self) -> AsyncMongoClient:
        """
        Get or create MongoDB client with connection pooling.

        Returns:
            AsyncMongoClient: Connected MongoDB client

        Raises:
            MongoDbConnectionError: If connection fails
        """
        if self._client is None:
            try:
                logger.debug(
                    "Establishing MongoDB connection to %s:%s", self.host, self.port
                )
                # This has connection pooling built in
                self._client = AsyncMongoClient(
                    self._url,
                    tlsCAFile=certifi.where(),
                )
                await self._client.admin.command("ping")
                logger.info(
                    "Successfully connected to MongoDB at %s:%s", self.host, self.port
                )
            except (
                ConnectionFailure,
                ServerSelectionTimeoutError,
                ConfigurationError,
            ) as e:
                logger.error(
                    "Failed to connect to MongoDB at %s:%s - %s",
                    self.host,
                    self.port,
                    e,
                )
                raise MongoDbConnectionError(
                    message=f"Could not connect to MongoDB: {self._url}.",
                    host=self.host,
                    port=self.port,
                ) from e

        return self._client

    async def _get_collection(self, collection_name: str, database_name: str):
        """
        Get MongoDB collection with connection management.

        Args:
            collection_name: Collection name
            database_name: Database name

        Returns:
            MongoDB collection object

        Raises:
            MongoDbTemporaryConnectionError: If connection issues occur
        """
        try:
            client = await self._get_client()
            db = client[database_name]
            collection = db[collection_name]
            logger.debug("Retrieved collection %s.%s", database_name, collection_name)
            return collection

        except (AutoReconnect, NetworkTimeout, NotPrimaryError) as e:
            logger.warning(
                "Temporary connection issue accessing %s.%s: %s",
                database_name,
                collection_name,
                e,
            )
            raise MongoDbTemporaryConnectionError(
                "Connection timeout",
                host=self.host,
                port=self.port,
                database_name=database_name,
                max_retries=3,
            ) from e

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
        Fetch documents in batches from MongoDB collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            query: Query filter
            projection: Fields to include/exclude
            batch_size: Documents per batch
            limit: Max documents to fetch (0 for no limit)
            skip: Documents to skip
            sort: Sort criteria

        Returns:
            AsyncGenerator yielding document batches

        Raises:
            MongoDbOperationError: If fetch fails
            MongoDbTemporaryOperationError: If temporary issues occur
        """

        async def generator() -> AsyncGenerator[List[Dict], None]:
            query_dict = query or {}
            projection_dict = projection or {}
            total_fetched = 0

            logger.debug(
                "Starting fetch from %s.%s with limit=%d, batch_size=%d",
                database_name,
                collection_name,
                limit,
                batch_size,
            )

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

                logger.debug(
                    "Completed fetch from %s.%s - %d documents retrieved",
                    database_name,
                    collection_name,
                    total_fetched,
                )

            except CursorNotFound as e:
                logger.error(
                    "Cursor not found for %s.%s: %s", database_name, collection_name, e
                )
                raise MongoDbOperationError(
                    message=f"Failed to fetch data: {str(e)}",
                    operation="fetch",
                    collection=collection_name,
                    query=query_dict,
                    details=str(e),
                ) from e

            except (OperationFailure, ExecutionTimeout, AutoReconnect) as e:
                logger.warning(
                    "Temporary fetch failure from %s.%s: %s",
                    database_name,
                    collection_name,
                    e,
                )
                raise MongoDbTemporaryOperationError(
                    message="Operation failed",
                    operation="fetch_from_db",
                    collection=collection_name,
                    query=query_dict,
                    max_retries=3,
                ) from e

        return generator()

    async def fetch_one_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict | None = None,
        projection: Dict | None = None,
    ) -> Optional[Dict | List]:
        """
        Fetch single document from MongoDB collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            query: Query filter
            projection: Fields to include/exclude

        Returns:
            Single document or None if not found

        Raises:
            MongoDbTemporaryOperationError: If operation fails
        """
        query = query or {}
        projection = projection or {}

        logger.debug(
            "Fetching single document from %s.%s", database_name, collection_name
        )

        try:
            collection = await self._get_collection(collection_name, database_name)
            result = await collection.find_one(query, projection)

            if result:
                logger.debug("Document found in %s.%s", database_name, collection_name)
            else:
                logger.debug(
                    "No document found in %s.%s matching query",
                    database_name,
                    collection_name,
                )

            return result

        except (OperationFailure, ExecutionTimeout, AutoReconnect) as e:
            logger.warning(
                "Temporary failure fetching from %s.%s: %s",
                database_name,
                collection_name,
                e,
            )
            raise MongoDbTemporaryOperationError(
                message="Operation failed",
                operation="fetch_one_from_db",
                collection=collection_name,
                query=query,
                max_retries=3,
            ) from e

    async def write_to_db(
        self,
        data: Union[Dict, list],
        collection_name: str,
        database_name: str,
        timestamp: bool = True,
    ) -> bool:
        """
        Write document(s) to MongoDB collection.

        Args:
            data: Document or list of documents to insert
            collection_name: Collection name
            database_name: Database name
            timestamp: Add created_at timestamp

        Returns:
            True if operation acknowledged

        Raises:
            MongoDbOperationError: If write fails permanently
            MongoDbTemporaryOperationError: If temporary issues occur
        """
        doc_count = len(data) if isinstance(data, list) else 1
        logger.debug(
            "Writing %d document(s) to %s.%s", doc_count, database_name, collection_name
        )

        try:
            collection = await self._get_collection(collection_name, database_name)

            if isinstance(data, list):
                if timestamp:
                    data = [
                        {**doc, "created_at": datetime.now(timezone.utc)}
                        for doc in data
                    ]
                result = await collection.insert_many(data)
                logger.info(
                    "Successfully wrote %d documents to %s.%s",
                    doc_count,
                    database_name,
                    collection_name,
                )
                return result.acknowledged

            if timestamp:
                data["created_at"] = datetime.now(timezone.utc)
            result = await collection.insert_one(data)
            logger.info(
                "Successfully wrote document to %s.%s", database_name, collection_name
            )
            return result.acknowledged

        except (DuplicateKeyError, DocumentTooLarge) as e:
            logger.error(
                "Write failed for %s.%s - %s", database_name, collection_name, e
            )
            raise MongoDbOperationError(
                message=f"Failed to write data: {str(e)}",
                operation="write_to_db",
                collection=collection_name,
                details=str(e),
            ) from e

        except (OperationFailure, AutoReconnect, WTimeoutError) as e:
            logger.warning(
                "Temporary write failure to %s.%s: %s",
                database_name,
                collection_name,
                e,
            )
            raise MongoDbTemporaryOperationError(
                message="Operation failed",
                operation="write_to_db",
                collection=collection_name,
                max_retries=3,
            ) from e

    async def update_one_to_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict,
        update: Dict,
        upsert: bool = False,
    ) -> bool:
        """
        Update single document in MongoDB collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            query: Query filter to identify document
            update: Update operations
            upsert: Create document if not found

        Returns:
            True if operation acknowledged

        Raises:
            MongoDbOperationError: If update fails permanently
            MongoDbTemporaryOperationError: If temporary issues occur
        """
        logger.debug(
            "Updating document in %s.%s (upsert=%s)",
            database_name,
            collection_name,
            upsert,
        )

        try:
            collection = await self._get_collection(collection_name, database_name)
            result = await collection.update_one(query, update, upsert=upsert)

            logger.info(
                "Update completed in %s.%s - matched: %d, modified: %d",
                database_name,
                collection_name,
                result.matched_count,
                result.modified_count,
            )

            return result.acknowledged

        except (DuplicateKeyError, DocumentTooLarge) as e:
            logger.error(
                "Update failed for %s.%s - %s", database_name, collection_name, e
            )
            raise MongoDbOperationError(
                message=f"Failed to write data: {str(e)}",
                operation="update_one_to_db",
                collection=collection_name,
                details=str(e),
            ) from e

        except (OperationFailure, AutoReconnect, WTimeoutError) as e:
            logger.warning(
                "Temporary update failure for %s.%s: %s",
                database_name,
                collection_name,
                e,
            )
            raise MongoDbTemporaryOperationError(
                message="Operation failed",
                operation="update_one_to_db",
                collection=collection_name,
                max_retries=3,
            ) from e

    async def run_aggregation(
        self,
        collection_name: str,
        database_name: str,
        pipeline: List[Any],
    ) -> List[Dict[str, List[Any]]]:
        """
        Execute aggregation pipeline on MongoDB collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            pipeline: Aggregation pipeline stages

        Returns:
            List of aggregation results

        Raises:
            MongoDbTemporaryOperationError: If aggregation fails
        """
        logger.debug(
            "Running aggregation on %s.%s with %d pipeline stages",
            database_name,
            collection_name,
            len(pipeline),
        )

        try:
            collection = await self._get_collection(collection_name, database_name)
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)

            logger.info(
                "Aggregation completed on %s.%s - %d results returned",
                database_name,
                collection_name,
                len(results),
            )
            return results

        except (OperationFailure, ExecutionTimeout, AutoReconnect) as e:
            logger.warning(
                "Aggregation failed on %s.%s: %s", database_name, collection_name, e
            )
            raise MongoDbTemporaryOperationError(
                message="Operation failed",
                operation="run_aggregation",
                collection=collection_name,
                max_retries=3,
            ) from e

    @property
    def parsed_url(self) -> ParseResult:
        """Parse MongoDB connection URL."""
        return urlparse(self._url)

    @property
    def host(self) -> Optional[str]:
        """Get MongoDB host from URL."""
        return self.parsed_url.hostname

    @property
    def port(self) -> Optional[int]:
        """Get MongoDB port from URL."""
        return self.parsed_url.port

    async def disconnect(self) -> None:
        """
        Safely close MongoDB connection asynchronously.
        """
        if self._client:
            try:
                await self._client.close()
                logger.info("Disconnected from MongoDB")
            except NetworkTimeout as e:
                logger.error("Timeout during MongoDB disconnect: %s", e)
            except ConnectionFailure as e:
                logger.error("Connection failure during MongoDB disconnect: %s", e)
            except PyMongoError as e:
                logger.error("PyMongo error during MongoDB disconnect: %s", e)
            finally:
                self._client = None

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self._url}>"

    def __str__(self) -> str:
        return "AsyncMongoDatabaseEngine"


mongo_database = AsyncMongoDatabaseEngine(getattr(settings, "MONGO_URL", None))
