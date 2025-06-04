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
from .integration.webhook import (
    WebhookEventNotSupportedError,
    WebhookJSONDecodeError,
    WebhookMissingFieldError,
    WebhookPayloadError,
    WebhookSchemaValidationError,
    WebhookValidationError,
)
from .library.scheduler import SchedulingError
from .repository.attempts import (
    InvalidAttemptInputError,
    InvalidScoreError,
    MaximumAttemptsExceededError,
)
from .repository.questions import QuestionNotFoundError
from .library.assessments import UserQuestionSetNotFoundError
from .library.course_sync import InvalidChangeDataTypeError

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
    # Scheduler
    "SchedulingError",
    # webhooks
    "WebhookValidationError",
    "WebhookPayloadError",
    "WebhookSchemaValidationError",
    "WebhookMissingFieldError",
    "WebhookJSONDecodeError",
    "WebhookEventNotSupportedError",
    #assessment
    "UserQuestionSetNotFoundError",
    #course sync
    "InvalidChangeDataTypeError",
]
