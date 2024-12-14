class VirtuEducateError(Exception):
    pass


class MongoDbConfigurationError(VirtuEducateError):
    """Raised when the MongoDB database engine is not configured correctly."""

    def __init__(self, message):
        super().__init__(message)


# TODO : need to do more explicit. Like pass the user data, question data etc.
class QuestionNotFoundError(VirtuEducateError):
    """Raised when a question cannot be found in the UserQuestionAttempts question metadata JSON field"""

    def __init__(self):
        super().__init__(
            "The specified question cannot be found in the UserQuestionAttempts question metadata JSON field"
        )
