from bot.stock_alert_bot import StockAlertBot
from config.settings import Settings
from db import create_db


def main():
    settings = Settings()
    db = create_db(settings)
    bot = StockAlertBot(settings, db)
    bot.run()


if __name__ == "__main__":
    main()
