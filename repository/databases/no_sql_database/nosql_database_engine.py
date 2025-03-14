"""
no_sql_database_engine.async_nosql_database_engine
~~~~~~~~~~~~~~~~~~

Asynchronous interface for all No Sql Database engines.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Union

log = logging.getLogger(__name__)


class AsyncBaseNoSqLDatabaseEngine(ABC):
    """Base interface for all asynchronous NoSQL database engines.

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
        """Fetch multiple documents from the database matching the given query."""
        raise NotImplementedError("Must implement fetch_from_db")

    @abstractmethod
    async def fetch_one_from_db(
        self,
        collection_name: str,
        database_name: str,
        query: Dict | None = None,
        projection: Dict | None = None,
    ) -> Any:
        """Fetch a single document from the database matching the given query."""
        raise NotImplementedError("Must implement fetch_one_from_db")

    @abstractmethod
    async def write_to_db(
        self,
        data: Union[Dict, list],
        collection_name: str,
        database_name: str,
        timestamp: bool = True,
    ) -> None:
        """Write data to the database."""
        raise NotImplementedError("Must implement write_to_db")

    @abstractmethod
    async def run_aggregation(
        self,
        collection_name: str,
        database_name: str,
        pipeline: List[Dict],
    ) -> Any:
        """Run an aggregation pipeline on the database."""
        raise NotImplementedError("Must implement run_aggregation")

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection."""
        raise NotImplementedError("Must implement disconnect")
