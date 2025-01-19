from typing import List, Optional
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from .basedb import BaseDB
from .models import Alert, WatchedKeyword, Portfolio
from .exceptions import DatabaseError, DuplicateKeywordError


class SQLiteDB(BaseDB):
    def __init__(self, db_path: str):
        """Initialize SQLite database connection"""
        try:
            self.db_path = db_path
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to connect to SQLite database: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DatabaseError(f"Transaction failed: {e}")
        finally:
            cursor.close()

    def setup_database(self) -> None:
        with self.transaction() as cursor:
            # Create watched keywords table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS watched_keywords (
                    keyword TEXT PRIMARY KEY,
                    last_check TIMESTAMP NOT NULL
                )
            """
            )

            # Create alert history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    INDEX idx_symbol_type (symbol, alert_type)
                )
            """
            )

    def add_alert(self, symbol: str, alert_type: str, price: float) -> None:
        with self.transaction() as cursor:
            cursor.execute(
                """INSERT INTO alert_history (symbol, alert_type, price, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (symbol, alert_type, price, datetime.now()),
            )

    def get_alerts(self) -> List[Alert]:
        with self.transaction() as cursor:
            cursor.execute("SELECT * FROM alert_history ORDER BY timestamp DESC")
            return [Alert(**dict(row)) for row in cursor.fetchall()]

    def check_duplicate_alert(self, symbol: str) -> Optional[Alert]:
        with self.transaction() as cursor:
            cursor.execute(
                """SELECT * FROM alert_history 
                   WHERE symbol = ?
                   AND timestamp > datetime('now', '-24 hours')
                   LIMIT 1""",
                (symbol,),
            )
            return bool(cursor.fetchone())

    def get_watched_keywords(self) -> List[WatchedKeyword]:
        with self.transaction() as cursor:
            cursor.execute("SELECT * FROM watched_keywords")
            return [WatchedKeyword(**dict(row)) for row in cursor.fetchall()]

    def exists_in_watched_keywords(self, keyword: str) -> bool:
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT 1 FROM watched_keywords WHERE keyword = ?", (keyword,)
            )
            return bool(cursor.fetchone())

    def add_to_watched_keywords(self, keyword: str) -> None:
        if self.exists_in_watched_keywords(keyword):
            raise DuplicateKeywordError(f"Keyword '{keyword}' already exists")

        with self.transaction() as cursor:
            cursor.execute(
                """INSERT INTO watched_keywords (keyword, last_check)
                   VALUES (?, ?)""",
                (keyword, datetime.now()),
            )

    def remove_from_watched_keywords(self, keyword: str) -> None:
        with self.transaction() as cursor:
            cursor.execute("DELETE FROM watched_keywords WHERE keyword = ?", (keyword,))

    def get_symbols(self) -> List[Portfolio]:
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT ticker, SUM(quantity) AS quantity FROM portfolio GROUP BY ticker ORDER BY ticker"
            )
            return [Portfolio(**row) for row in cursor.fetchall()]

    def close(self) -> None:
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
