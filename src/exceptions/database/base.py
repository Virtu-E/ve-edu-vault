from src.exceptions import VirtuEducateSystemError


class DatabaseError(VirtuEducateSystemError):
    """
    Base exception for database-related operations.
    Simple base - specific database errors add their own context.
    """

    pass
