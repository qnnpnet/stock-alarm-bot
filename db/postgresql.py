import traceback
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from contextlib import contextmanager
from .basedb import BaseDB
from .models import Alert, WatchedKeyword
from .exceptions import DatabaseError, DuplicateKeywordError


class PostgreSQLDB(BaseDB):
    def __init__(self, connection_config: dict):
        """Initialize PostgreSQL database connection"""
        try:
            self.conn = psycopg2.connect(
                **connection_config, cursor_factory=RealDictCursor
            )
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            traceback.print_exc()
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
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """
            )

            # Create index for alert history
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alert_history_symbol_type
                ON alert_history (symbol, alert_type)
            """
            )

    # PostgreSQL specific implementations follow the same pattern as SQLite
    # but use %s instead of ? for parameter substitution
    def add_alert(self, symbol: str, alert_type: str, price: float) -> None:
        with self.transaction() as cursor:
            cursor.execute(
                """INSERT INTO alert_history (symbol, alert_type, price, timestamp)
                   VALUES (%s, %s, %s, %s)""",
                (symbol, alert_type, price, datetime.now()),
            )

    def get_alerts(self) -> List[Alert]:
        with self.transaction() as cursor:
            cursor.execute("SELECT * FROM alert_history ORDER BY timestamp DESC")
            return [Alert(**row) for row in cursor.fetchall()]

    def check_duplicate_alert(self, symbol: str) -> Optional[Alert]:
        with self.transaction() as cursor:
            cursor.execute(
                """SELECT * FROM alert_history 
                   WHERE symbol = %s
                   AND timestamp > NOW() - INTERVAL '24 hours'
                   LIMIT 1""",
                (symbol,),
            )
            return bool(cursor.fetchone())

    def get_watched_keywords(self) -> List[WatchedKeyword]:
        with self.transaction() as cursor:
            cursor.execute("SELECT * FROM watched_keywords")
            return [WatchedKeyword(**row) for row in cursor.fetchall()]

    def exists_in_watched_keywords(self, keyword: str) -> bool:
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT 1 FROM watched_keywords WHERE keyword = %s", (keyword,)
            )
            return bool(cursor.fetchone())

    def add_to_watched_keywords(self, keyword: str) -> None:
        if self.exists_in_watched_keywords(keyword):
            raise DuplicateKeywordError(f"Keyword '{keyword}' already exists")

        with self.transaction() as cursor:
            cursor.execute(
                """INSERT INTO watched_keywords (keyword, last_check)
                   VALUES (%s, %s)""",
                (keyword, datetime.now()),
            )

    def remove_from_watched_keywords(self, keyword: str) -> None:
        with self.transaction() as cursor:
            cursor.execute(
                "DELETE FROM watched_keywords WHERE keyword = %s", (keyword,)
            )

    def get_symbols(self):
        with self.transaction() as cursor:
            cursor.execute("SELECT DISTINCT ticker FROM portfolio")
            return [row["ticker"] for row in cursor.fetchall()]

    def close(self) -> None:
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
