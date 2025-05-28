class QuestionAttemptError(Exception):
    """Base exception for question attempt operations"""

    pass


class QuestionNotFoundError(QuestionAttemptError):
    """Raised when question is not found"""

    pass
