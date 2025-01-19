# db/basedb.py


class BaseDB:
    def __init__(self, connection_config):
        self.connection_config = connection_config

    def setup_database(self):
        raise NotImplementedError("setup_database must be implemented")

    def create_watched_keywords_table(self):
        raise NotImplementedError("create_watched_keywords_table must be implemented")

    def create_alert_history_table(self):
        raise NotImplementedError("create_alert_history_table must be implemented")

    def add_alert(self, keyword, alert_type, price):
        raise NotImplementedError("add_alert must be implemented")

    def get_alerts(self):
        raise NotImplementedError("get_alerts must be implemented")

    def find_duplicate(self, keyword, alert_type):
        raise NotImplementedError("find_duplicate must be implemented")

    def get_keywords_from_watched_keywords(self):
        raise NotImplementedError(
            "get_keywords_from_watched_keywords must be implemented"
        )

    def get_stock_tickers_from_portfolio(self):
        raise NotImplementedError(
            "get_stock_tickers_from_portfolio must be implemented"
        )

    def exists_in_watched_keywords(self, keyword):
        raise NotImplementedError("exists_in_watched_keywords must be implemented")

    def add_to_watched_keywords(self, keyword):
        raise NotImplementedError("add_to_watched_keywords must be implemented")

    def remove_from_watched_keywords(self, keyword):
        raise NotImplementedError("remove_from_watched_keywords must be implemented")

    def close(self):
        raise NotImplementedError("close must be implemented")
