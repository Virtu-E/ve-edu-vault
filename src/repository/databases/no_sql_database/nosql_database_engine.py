"""
no_sql_database_engine.async_nosql_database_engine
~~~~~~~~~~~~~~~~~~

Asynchronous interface for all NoSQL database engines.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Union

log = logging.getLogger(__name__)


class AsyncBaseNoSqLDatabaseEngine(ABC):
    """
    Base interface for all asynchronous NoSQL database engines.

    This abstract class defines a standard interface for interacting with NoSQL databases
    in an asynchronous manner. Concrete implementations should handle database-specific
    connection management and operation execution while adhering to this interface.
    """

    @abstractmethod
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
        Fetch multiple documents from the database that match the given query.

        Args:
            collection_name: Name of the collection to query.
            database_name: Name of the database to connect to.
            query: Filter to apply when querying documents.
            projection: Fields to include or exclude in the returned documents.
            batch_size: Number of documents to yield per batch.
            limit: Maximum number of documents to return.
            skip: Number of documents to skip from the beginning.
            sort: List of sort conditions as (field, direction) tuples.

        Returns:
            An asynchronous generator yielding lists of matching documents.
        """
        raise NotImplementedError("Must implement fetch_from_db")

    @abstractmethod
    async def fetch_one_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict | None = None,
        projection: Dict | None = None,
    ) -> Any:
        """
        Fetch a single document from the database matching the given query.

        Args:
            collection_name: Name of the collection to query.
            database_name: Name of the database to connect to.
            query: Filter to identify the document.
            projection: Fields to include or exclude in the returned document.

        Returns:
            The first document matching the query, or None if no match is found.
        """
        raise NotImplementedError("Must implement fetch_one_from_db")

    @abstractmethod
    async def write_to_db(
        self,
        data: Union[Dict, list],
        collection_name: str,
        database_name: str,
        timestamp: bool = True,
    ) -> bool:
        """
        Insert one or more documents into the database.

        Args:
            data: A single document or a list of documents to insert.
            collection_name: Name of the collection to write to.
            database_name: Name of the database to connect to.
            timestamp: Whether to automatically add timestamps to the documents.

        Returns:
            bool: True if operation was acknowledged, False otherwise.
        """
        raise NotImplementedError("Must implement write_to_db")

    @abstractmethod
    async def update_one_to_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict,
        update: Dict,
        upsert: bool = False,
    ) -> bool:
        """
        Update a single document in the database matching the given query.

        Args:
            collection_name: Name of the collection.
            database_name: Name of the database.
            query: MongoDB query filter to identify the document.
            update: Update operations to apply to the document.
            upsert: If True, create a new document when no document matches the query.

        Returns:
            bool: True if operation was acknowledged, False otherwise.
        """
        raise NotImplementedError("Must implement update_one")

    @abstractmethod
    async def run_aggregation(
        self,
        collection_name: str,
        database_name: str,
        pipeline: List[Dict],
    ) -> Any:
        """
        Run an aggregation pipeline on the specified collection.

        Args:
            collection_name: Name of the collection to aggregate.
            database_name: Name of the database to connect to.
            pipeline: List of aggregation stages to execute.

        Returns:
            The result of the aggregation operation.
        """
        raise NotImplementedError("Must implement run_aggregation")

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection to the database.

        Should ensure that all active connections or sessions are properly closed.
        """
        raise NotImplementedError("Must implement disconnect")
