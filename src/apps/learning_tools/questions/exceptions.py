class QuestionAttemptError(Exception):
    """Base exception for question attempt operations"""

    pass


class GradingError(QuestionAttemptError):
    """Raised when grading fails"""

    pass


class MaximumAttemptsError(GradingError):
    """Raised when the user has exceeded the maximum number of attempts"""

    pass


class QuestionNotFoundError(QuestionAttemptError):
    """Raised when question is not found"""

    pass


class ConfigurationError(QuestionAttemptError):
    """Raised when configuration is invalid"""

    pass
