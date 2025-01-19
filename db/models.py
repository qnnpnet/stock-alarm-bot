from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Alert(BaseModel):
    symbol: str
    alert_type: str
    price: float
    timestamp: datetime


class WatchedKeyword(BaseModel):
    keyword: str
    last_check: datetime


# db/exceptions.py
class DatabaseError(Exception):
    """Base exception for database errors"""

    pass


class DuplicateKeywordError(DatabaseError):
    """Raised when attempting to add a duplicate keyword"""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""

    pass
