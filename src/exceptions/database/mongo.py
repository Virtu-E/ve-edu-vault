from typing import Optional

from .base import DatabaseError


class MongoDbError(DatabaseError): ...


class MongoDbConfigurationError(MongoDbError):
    """
    Raised when MongoDB database engine is not configured correctly.
    """

    def __init__(
        self,
        message: str = "MongoDB configuration is invalid",
        missing_config: Optional[str] = None,
        config_file: Optional[str] = None,
        expected_format: Optional[str] = None,
        current_value: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)

        self.error_code = "500"

        self.context = {
            k: v
            for k, v in {
                "missing_config": missing_config,
                "config_file": config_file,
                "expected_format": expected_format,
                "current_value": current_value,
                "error_type": "MONGODB_CONFIG_ERROR",
            }.items()
            if v is not None
        }


class MongoDbConnectionError(MongoDbError):
    """
    Raised when connection to MongoDB fails permanently.

    This represents non-recoverable connection issues like:
    - Invalid credentials
    - Wrong host/port configuration
    - SSL/TLS configuration errors
    - Network unreachable errors
    """

    def __init__(
        self,
        message: str = "Failed to connect to MongoDB",
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)

        self.error_code = "500"

        self.context = {
            k: v
            for k, v in {
                "host": host,
                "port": port,
                "database": database,
                "timeout_seconds": timeout_seconds,
                "error_type": "MONGODB_CONNECTION_ERROR",
                "recoverable": False,
            }.items()
            if v is not None
        }


class MongoDbTemporaryConnectionError(MongoDbError):
    """
    Raised when connection to MongoDB fails temporarily and can be retried.

    This represents recoverable connection issues like:
    - Network timeouts
    - Temporary DNS resolution failures
    - Connection pool exhaustion
    - Server temporarily unavailable
    - Rate limiting
    """

    def __init__(
        self,
        message: str = "Temporary MongoDB connection failure",
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        retry_after_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        current_retry: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)

        self.error_code = "500"

        self.context = {
            k: v
            for k, v in {
                "host": host,
                "port": port,
                "database": database,
                "timeout_seconds": timeout_seconds,
                "retry_after_seconds": retry_after_seconds,
                "max_retries": max_retries,
                "current_retry": current_retry,
                "error_type": "MONGODB_TEMPORARY_CONNECTION_ERROR",
                "recoverable": True,
            }.items()
            if v is not None
        }


class MongoDbOperationError(MongoDbError):
    """Raised when MongoDB operations fail."""

    def __init__(
        self,
        message: str = "MongoDB operation failed",
        operation: Optional[str] = None,
        collection: Optional[str] = None,
        query: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)

        self.error_code = "500"

        self.context = {
            k: v
            for k, v in {
                "operation": operation,
                "collection": collection,
                "query": str(query) if query else None,
                "error_type": "MONGODB_OPERATION_ERROR",
            }.items()
            if v is not None
        }


class MongoDbTemporaryOperationError(MongoDbError):
    """
    Raised when MongoDB operations fail temporarily and can be retried.

    This represents recoverable operation issues like:
    - Write conflicts
    - Lock timeouts
    - Temporary resource exhaustion
    - Network interruptions during operation
    - Replica set failover in progress
    """

    def __init__(
        self,
        message: str = "MongoDB operation temporarily failed",
        operation: Optional[str] = None,
        collection: Optional[str] = None,
        query: Optional[dict] = None,
        retry_after_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        current_retry: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)

        self.error_code = "500"

        self.context = {
            k: v
            for k, v in {
                "operation": operation,
                "collection": collection,
                "query": str(query) if query else None,
                "retry_after_seconds": retry_after_seconds,
                "max_retries": max_retries,
                "current_retry": current_retry,
                "error_type": "MONGODB_TEMPORARY_OPERATION_ERROR",
                "recoverable": True,
            }.items()
            if v is not None
        }
