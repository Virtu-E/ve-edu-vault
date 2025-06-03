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
from .repository.attempts import (
    InvalidAttemptInputError,
    InvalidScoreError,
    MaximumAttemptsExceededError,
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
    # Attempts
    "MaximumAttemptsExceededError",
    "InvalidAttemptInputError",
    "InvalidScoreError",
]
