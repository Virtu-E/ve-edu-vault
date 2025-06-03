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
from .repository.questions import QuestionNotFoundError

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
    # Question
    "QuestionNotFoundError",
]
