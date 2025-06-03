from .base import (
    VirtuEducateBusinessError,
    VirtuEducateError,
    VirtuEducateIntegrationError,
    VirtuEducateSystemError,
    VirtuEducateValidationError,
)
from .database.mongo import (
    MongoDbConfigurationError,
    MongoDbConnectionError,
    MongoDbOperationError,
    MongoDbTemporaryConnectionError,
    MongoDbTemporaryOperationError,
)

__all__ = [
    # Base
    "VirtuEducateError",
    "VirtuEducateBusinessError",
    "VirtuEducateSystemError",
    "VirtuEducateValidationError",
    "VirtuEducateIntegrationError",
    # Mongo DB
    "MongoDbConfigurationError",
    "MongoDbConnectionError",
    "MongoDbTemporaryConnectionError",
    "MongoDbOperationError",
    "MongoDbTemporaryOperationError",
]
