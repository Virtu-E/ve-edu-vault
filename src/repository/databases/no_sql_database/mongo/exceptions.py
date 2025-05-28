"""
no_sql_database.exceptions
~~~~~~~~~~~~~~

Custom Exceptions for the no sql database package
"""

from src.exceptions import VirtuEducateError


class DatabaseError(VirtuEducateError):
    """Base exception for all database-related operations."""

    def __init__(self, message="A database error occurred", *args, **kwargs):
        self.message = message
        super().__init__(self.message, *args)
        self.details = kwargs.get("details")
        self.operation = kwargs.get("operation")
        self.collection = kwargs.get("collection")
        self.query = kwargs.get("query")

    def __str__(self):
        base_msg = f"{self.__class__.__name__}: {self.message}"
        if self.operation:
            base_msg += f" (Operation: {self.operation})"
        if self.collection:
            base_msg += f" (Collection: {self.collection})"
        if self.details:
            base_msg += f"\nDetails: {self.details}"
        return base_msg


class MongoDbConfigurationError(DatabaseError):
    """Raised when the MongoDB database engine is not configured correctly."""

    pass


class MongoDbConnectionError(DatabaseError):
    """Raised when connection to MongoDB fails."""

    pass


class MongoDbOperationError(DatabaseError):
    """Raised when MongoDB operations fail."""

    pass
