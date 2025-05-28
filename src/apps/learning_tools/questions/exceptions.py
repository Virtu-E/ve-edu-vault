from src.repository.question_repository.exceptions import QuestionAttemptError


class GradingError(QuestionAttemptError):
    """Raised when grading fails"""

    pass


class MaximumAttemptsError(GradingError):
    """Raised when the user has exceeded the maximum number of attempts"""

    pass



class ConfigurationError(QuestionAttemptError):
    """Raised when configuration is invalid"""

    pass
