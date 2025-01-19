import psycopg2
from datetime import datetime

from db.basedb import BaseDB


class PostgreSQLDB(BaseDB):
    def __init__(
        self,
        connection_config={
            "host": "localhost",
            "port": 5432,
            "dbname": "stock_alert_bot",
            "user": "postgres",
            "password": "postgres",
        },
    ):
        db_uri = f"postgresql://{connection_config['user']}:{connection_config['password']}@{connection_config['host']}:{connection_config['port']}/{connection_config['dbname']}"
        self.conn = psycopg2.connect(db_uri)
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
            "INSERT INTO watched_keywords (keyword, last_check) VALUES (%s, %s)",
            (keyword, datetime.now()),
        )
        self.conn.commit()

    def remove_from_watched_keywords(self, keyword):
        self.cursor.execute(
            "DELETE FROM watched_keywords WHERE keyword = %s", (keyword,)
        )
        self.conn.commit()

    def get_stock_tickers_from_portfolio(self):
        self.cursor.execute("SELECT distinct ticker FROM portfolio")
        return self.cursor.fetchall()

    def get_keywords_from_watched_keywords(self):
        self.cursor.execute("SELECT keyword, last_check FROM watched_keywords")
        return self.cursor.fetchall()

    def exists_in_watched_keywords(self, keyword) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM watched_keywords WHERE keyword = %s", (keyword,)
        )
        return bool(self.cursor.fetchone())

    def add_alert(self, symbol, alert_type, price):
        self.cursor.execute(
            "INSERT INTO alert_history (symbol, alert_type, price, timestamp) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
            (symbol, alert_type, price),
        )
        self.conn.commit()

    def get_alerts(self):
        self.cursor.execute("SELECT * FROM alert_history")
        return self.cursor.fetchall()

    def find_duplicate(self, symbol, alert_type):
        self.cursor.execute(
            "SELECT * FROM alert_history WHERE symbol = %s AND alert_type = %s AND timestamp > CURRENT_TIMESTAMP - INTERVAL '10 hours'",
            (symbol, alert_type),
        )
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
