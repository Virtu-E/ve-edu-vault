from typing import Optional

from .base import DatabaseError


class MongoDbError(DatabaseError):
    """Base class for MongoDB-specific errors."""

    pass


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

        self.missing_config = missing_config
        self.config_file = config_file
        self.expected_format = expected_format
        self.current_value = current_value
        self.error_code = "MONGODB_CONFIG_ERROR"

        self.context = {
            "error_code": self.error_code,
            "missing_config": missing_config,
            "config_file": config_file,
            "expected_format": expected_format,
            "current_value": current_value,
            "error_type": "configuration",
        }

        self.context = {k: v for k, v in self.context.items() if v is not None}

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "type": self.__class__.__name__,
        }

    def __str__(self):
        if self.missing_config:
            return f"{self.message} (missing: {self.missing_config})"
        return self.message


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

        self.host = host
        self.port = port
        self.database = database
        self.timeout_seconds = timeout_seconds
        self.error_code = "MONGODB_CONNECTION_ERROR"
        self.recoverable = False  # Mark as non-recoverable

        self.context = {
            "error_code": self.error_code,
            "host": host,
            "port": port,
            "database": database,
            "timeout_seconds": timeout_seconds,
            "error_type": "connection",
            "recoverable": False,
        }

        self.context = {k: v for k, v in self.context.items() if v is not None}


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

        self.host = host
        self.port = port
        self.database = database
        self.timeout_seconds = timeout_seconds
        self.retry_after_seconds = retry_after_seconds
        self.max_retries = max_retries
        self.current_retry = current_retry
        self.error_code = "MONGODB_TEMPORARY_CONNECTION_ERROR"
        self.recoverable = True  # Mark as recoverable

        self.context = {
            "error_code": self.error_code,
            "host": host,
            "port": port,
            "database": database,
            "timeout_seconds": timeout_seconds,
            "retry_after_seconds": retry_after_seconds,
            "max_retries": max_retries,
            "current_retry": current_retry,
            "error_type": "temporary_connection",
            "recoverable": True,
        }

        self.context = {k: v for k, v in self.context.items() if v is not None}

    def can_retry(self) -> bool:
        """Check if this error can be retried."""
        if self.max_retries is None or self.current_retry is None:
            return True
        return self.current_retry < self.max_retries

    def get_retry_delay(self) -> int:
        """Get suggested retry delay in seconds."""
        return self.retry_after_seconds or 1


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

        self.operation = operation
        self.collection = collection
        self.query = query
        self.error_code = "MONGODB_OPERATION_ERROR"

        self.context = {
            "error_code": self.error_code,
            "operation": operation,
            "collection": collection,
            "query": str(query) if query else None,
            "error_type": "operation",
        }

        self.context = {k: v for k, v in self.context.items() if v is not None}


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

        self.operation = operation
        self.collection = collection
        self.query = query
        self.retry_after_seconds = retry_after_seconds
        self.max_retries = max_retries
        self.current_retry = current_retry
        self.error_code = "MONGODB_TEMPORARY_OPERATION_ERROR"
        self.recoverable = True

        self.context = {
            "error_code": self.error_code,
            "operation": operation,
            "collection": collection,
            "query": str(query) if query else None,
            "retry_after_seconds": retry_after_seconds,
            "max_retries": max_retries,
            "current_retry": current_retry,
            "error_type": "temporary_operation",
            "recoverable": True,
        }

        self.context = {k: v for k, v in self.context.items() if v is not None}

    def can_retry(self) -> bool:
        """Check if this operation can be retried."""
        if self.max_retries is None or self.current_retry is None:
            return True
        return self.current_retry < self.max_retries

    def get_retry_delay(self) -> int:
        """Get suggested retry delay in seconds."""
        return self.retry_after_seconds or 1
