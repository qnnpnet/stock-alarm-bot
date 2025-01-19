class DatabaseError(Exception):
    """Base exception for database errors"""

    pass


class DuplicateKeywordError(DatabaseError):
    """Raised when attempting to add a duplicate keyword"""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""

    pass
