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


class MongoDbConnectionError(DatabaseError):
    """Raised when connection to MongoDB fails."""

    def __init__(self, message):
        super().__init__(message)


class MongoDbOperationError(DatabaseError):
    """Raised when MongoDB operations fail."""

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


class DatabaseUpdateError(DatabaseError):
    """Raised when there is an error updating, inserting, or deleting data in the database."""

    def __init__(self, message="Error performing a database update operation", *args):
        self.message = message
        super().__init__(self.message, *args)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class ParsingError(VirtuEducateError):
    """Base exception for all parsing-related errors."""

    def __init__(self, message="A parsing error occurred", *args):
        self.message = message
        super().__init__(self.message, *args)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class VersionParsingError(ParsingError):
    """Raised when a version string cannot be parsed into a valid version tuple."""

    def __init__(self, version, message="Invalid version format"):
        self.version = version
        self.message = f"{message}: {version}"
        super().__init__(self.message)


class JsonParsingError(ParsingError):
    """Raised when a JSON string cannot be parsed."""

    def __init__(self, json_string, message="Invalid JSON format"):
        self.json_string = json_string
        self.message = f"{message}: {json_string}"
        super().__init__(self.message)


class TypeValidationError(ParsingError):
    """Raised when an error occurs during type validation."""

    def __init__(self, field_name, message="Validation failed for field"):
        self.field_name = field_name
        self.message = f"{message}: {field_name}"
        super().__init__(self.message)


class XmlParsingError(ParsingError):
    """Raised when an XML string cannot be parsed."""

    def __init__(self, xml_string, message="Invalid XML format"):
        self.xml_string = xml_string
        self.message = f"{message}: {xml_string}"
        super().__init__(self.message)


class InsufficientQuestionsError(QuestionFetchError):
    """Exception raised when there are not enough questions available"""

    pass


# TODO : change the base class below to a more appropriate and meaningful name
class ValidationError(VirtuEducateError):
    """Exception raised for validation errors."""

    def __init__(self, message="Validation error occurred", *args):
        self.message = message
        super().__init__(self.message, *args)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class QuestionNotFoundError(ValidationError):
    """Raised when a question is not found in a user's question set."""

    def __init__(self, question_id, username, message="Question not found"):
        self.question_id = question_id
        self.username = username
        self.message = (
            f"{message}: Question ID '{question_id}' not found for user '{username}'"
        )
        super().__init__(self.message)


class InvalidQuestionConfiguration(VirtuEducateError):
    """Raised when we cant find question attempt data in the metadata"""

    def __init__(self, parameter, message="Invalid parameter"):
        self.parameter = parameter
        self.message = f"{message}: '{parameter}'"
        super().__init__(self.message)


class InvalidParameterError(VirtuEducateError):
    """Raised when there are missing or invalid parameters in a request."""

    def __init__(self, parameter, message="Invalid parameter"):
        self.parameter = parameter
        self.message = f"{message}: '{parameter}'"
        super().__init__(self.message)


class OrchestrationError(Exception):
    """Custom exception for orchestration related errors"""

    pass
