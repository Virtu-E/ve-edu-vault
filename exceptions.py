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


class XmlParsingError(ParsingError):
    """Raised when an XML string cannot be parsed."""

    def __init__(self, xml_string, message="Invalid XML format"):
        self.xml_string = xml_string
        self.message = f"{message}: {xml_string}"
        super().__init__(self.message)


class InsufficientQuestionsError(QuestionFetchError):
    """Exception raised when there are not enough questions available"""

    pass
