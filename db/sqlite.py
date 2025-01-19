import sqlite3
from datetime import datetime

from db.basedb import BaseDB


class SQLiteDB(BaseDB):
    def __init__(self, db_name="watched_keywords.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def setup_database(self):
        self.create_watched_keywords_table()
        self.create_alert_history_table()

    def create_watched_keywords_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS watched_keywords
            (keyword TEXT PRIMARY KEY, last_check TIMESTAMP)
        """
        )
        self.conn.commit()

    def create_alert_history_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_history
            (symbol TEXT, alert_type TEXT, price REAL, timestamp TIMESTAMP)
        """
        )
        self.conn.commit()

    def add_to_watched_keywords(self, keyword):
        self.cursor.execute(
            "INSERT OR REPLACE INTO watched_keywords (keyword, last_check) VALUES (?, ?)",
            (keyword, datetime.now()),
        )
        self.conn.commit()

    def remove_from_watched_keywords(self, keyword):
        self.cursor.execute(
            "DELETE FROM watched_keywords WHERE keyword = ?", (keyword,)
        )
        self.conn.commit()

    def get_keywords_from_watched_keywords(self):
        self.cursor.execute("SELECT * FROM watched_keywords")
        return self.cursor.fetchall()

    def exists_in_watched_keywords(self, keyword) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM watched_keywords WHERE keyword = ?", (keyword,)
        )
        return bool(self.cursor.fetchone())

    def add_alert(self, symbol, alert_type, price):
        self.cursor.execute(
            "INSERT INTO alert_history (symbol, alert_type, price, timestamp) VALUES (?, ?, ?, datetime('now'))",
            (symbol, alert_type, price),
        )
        self.conn.commit()

    def get_alerts(self):
        self.cursor.execute("SELECT * FROM alert_history")
        return self.cursor.fetchall()

    def find_duplicate(self, symbol, alert_type):
        self.cursor.execute(
            "SELECT * FROM alert_history WHERE symbol = ? AND alert_type = ? AND timestamp > datetime('now', '-10 hours')",
            (symbol, alert_type),
        )
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
