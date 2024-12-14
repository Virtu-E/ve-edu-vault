class VirtuEducateError(Exception):
    pass


class MongoDbConfigurationError(VirtuEducateError):
    """Raised when the MongoDB database engine is not configured correctly."""

    def __init__(self, message):
        super().__init__(message)
