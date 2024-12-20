class VirtuEducateError(Exception):
    pass


class DatabaseError(VirtuEducateError):
    """Base exception for all database-related operations.

    Inherit from this class to handle database-specific errors across different databases.
    """

    def __init__(self, message="A database error occurred", *args):
        self.message = message
        super().__init__(self.message, *args)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class MongoDbConfigurationError(DatabaseError):
    """Raised when the MongoDB database engine is not configured correctly."""

    def __init__(self, message):
        super().__init__(message)


class QuestionFetchError(DatabaseError):
    """Raised when there is an error fetching questions from MongoDB."""

    def __init__(self, message="Error fetching questions from MongoDB", *args):
        self.message = message
        super().__init__(self.message, *args)


class DatabaseQueryError(DatabaseError):
    """Raised when there is an error querying the database."""

    def __init__(self, message="Error querying the database", *args):
        self.message = message
        super().__init__(self.message, *args)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"
