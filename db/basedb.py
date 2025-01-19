from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from .models import Alert, WatchedKeyword
from .exceptions import DatabaseError, DuplicateKeywordError


class BaseDB(ABC):
    """Abstract base class for database implementations"""

    @abstractmethod
    def setup_database(self) -> None:
        """Initialize database schema"""
        pass

    @abstractmethod
    def add_alert(self, symbol: str, alert_type: str, price: float) -> None:
        """Add a new alert to the database"""
        pass

    @abstractmethod
    def get_alerts(self) -> List[Alert]:
        """Retrieve all alerts"""
        pass

    @abstractmethod
    def check_duplicate_alert(self, symbol: str) -> Optional[Alert]:
        """Find duplicate alerts within the last 24 hours"""
        pass

    @abstractmethod
    def get_watched_keywords(self) -> List[WatchedKeyword]:
        """Get all watched keywords"""
        pass

    @abstractmethod
    def exists_in_watched_keywords(self, keyword: str) -> bool:
        """Check if a keyword exists in watched keywords"""
        pass

    @abstractmethod
    def add_to_watched_keywords(self, keyword: str) -> None:
        """Add a new keyword to watched keywords"""
        pass

    @abstractmethod
    def remove_from_watched_keywords(self, keyword: str) -> None:
        """Remove a keyword from watched keywords"""
        pass

    @abstractmethod
    def get_symbols(self) -> List[str]:
        """Get all symbols"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection"""
        pass
