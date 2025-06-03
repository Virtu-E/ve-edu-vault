import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

log = logging.getLogger(__name__)


class AsyncAbstractNoSqLDatabaseEngine(ABC):
    """
    Base interface for asynchronous NoSQL database engines.

    Defines standard interface for NoSQL database operations with
    connection management and error handling.
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
        Fetch documents in batches from database collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            query: Query filter
            projection: Fields to include/exclude
            batch_size: Documents per batch
            limit: Max documents to fetch (0 for no limit)
            skip: Documents to skip
            sort: Sort criteria as (field, direction) tuples

        Returns:
            AsyncGenerator yielding document batches
        """
        raise NotImplementedError("Must implement fetch_from_db")

    @abstractmethod
    async def fetch_one_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict | None = None,
        projection: Dict | None = None,
    ) -> Optional[Dict | List]:
        """
        Fetch single document from database collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            query: Query filter
            projection: Fields to include/exclude

        Returns:
            Single document or None if not found
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
        Write document(s) to database collection.

        Args:
            data: Document or list of documents to insert
            collection_name: Collection name
            database_name: Database name
            timestamp: Add timestamp to documents

        Returns:
            True if operation acknowledged
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
        Update single document in database collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            query: Query filter to identify document
            update: Update operations
            upsert: Create document if not found

        Returns:
            True if operation acknowledged
        """
        raise NotImplementedError("Must implement update_one_to_db")

    @abstractmethod
    async def run_aggregation(
        self,
        collection_name: str,
        database_name: str,
        pipeline: List[Any],
    ) -> List[Dict[str, List[Any]]]:
        """
        Execute aggregation pipeline on database collection.

        Args:
            collection_name: Collection name
            database_name: Database name
            pipeline: Aggregation pipeline stages

        Returns:
            List of aggregation results
        """
        raise NotImplementedError("Must implement run_aggregation")

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection to the database.

        Should ensure that all active connections or sessions are properly closed.
        """
        raise NotImplementedError("Must implement disconnect")
