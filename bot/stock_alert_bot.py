import traceback
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from services.stock_service import StockService
from services.news_service import NewsService
from db.basedb import BaseDB
from utils.logger import setup_logger
from config.settings import Settings
import pandas as pd


class StockAlertBot:
    def __init__(self, settings: Settings, db: BaseDB):
        self.settings = settings
        self.db = db
        self.stock_service = StockService()
        self.news_service = NewsService()
        self.logger = setup_logger()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        context.application.bot_data["chat_id"] = chat_id
        self.logger.info(f"New user started the bot (Chat ID: {chat_id})")

        await update.message.reply_text(
            "Stock Alarm Bot Started!\n"
            "/add <keyword> - Add keyword to watchlist\n"
            "/remove <keyword> - Remove keyword from watchlist\n"
            "/keywords - View keywords\n"
            "/portfolio - View your portfolio\n"
        )

    async def add_keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /add <keyword>")
            return

        keyword = " ".join(context.args)
        try:
            if self.db.exists_in_watched_keywords(keyword):
                await update.message.reply_text(f"{keyword} is already being watched.")
                return

            self.db.add_to_watched_keywords(keyword)
            chart = self.stock_service.generate_chart(
                keyword, self.stock_service.get_stock_data(keyword)
            )
            await update.message.reply_photo(
                photo=chart, caption=f"📈 Added {keyword} to watchlist."
            )
        except Exception as e:
            self.logger.error(f"Failed to add keyword: {str(e)}")
            await update.message.reply_text(f"Failed to add keyword: {str(e)}")

    async def remove_keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Remove a keyword from the watchlist
        """
        if not context.args:
            await update.message.reply_text("Usage: /remove <keyword>")
            return

        keyword = " ".join(context.args)
        try:
            if not self.db.exists_in_watched_keywords(keyword):
                await update.message.reply_text(f"{keyword} is not in your watchlist.")
                return

            self.db.remove_from_watched_keywords(keyword)
            await update.message.reply_text(f"❌ Removed {keyword} from watchlist.")
            self.logger.info(f"Removed keyword: {keyword}")

        except Exception as e:
            self.logger.error(f"Failed to remove keyword: {str(e)}")
            await update.message.reply_text(f"Failed to remove keyword: {str(e)}")

    async def list_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        List all keywords in the watchlist
        """
        try:
            keywords = [keyword.keyword for keyword in self.db.get_watched_keywords()]

            if not keywords:
                await update.message.reply_text("Your watchlist is empty.")
                return

            # Simply show the keywords and number of items in the watchlist
            message = f"📊 Watchlist:\n\n"
            for keyword in keywords:
                message += f"- {keyword}\n"
            message += f"\nTotal: {len(keywords)} items"

            # # Create a formatted message with stock data for each keyword
            # message = "📊 Your Watchlist:\n\n"
            # for keyword in keywords:
            #     try:
            #         stock_data = self.stock_service.get_stock_data(keyword)
            #         if not stock_data.empty:
            #             current_price = stock_data["Close"].iloc[-1]
            #             price_change = (
            #                 stock_data["Close"].iloc[-1] - stock_data["Close"].iloc[-2]
            #             )
            #             price_change_pct = (
            #                 price_change / stock_data["Close"].iloc[-2]
            #             ) * 100

            #             # Add emoji based on price movement
            #             emoji = (
            #                 "🔺"
            #                 if price_change > 0
            #                 else "🔻" if price_change < 0 else "➖"
            #             )

            #             message += (
            #                 f"{emoji} {keyword}\n"
            #                 f"    Price: ${current_price:.2f}\n"
            #                 f"    Change: {price_change_pct:+.2f}%\n\n"
            #             )
            #         else:
            #             message += f"❓ {keyword} (No data available)\n\n"

            #     except Exception as e:
            #         self.logger.warning(f"Failed to get data for {keyword}: {str(e)}")
            #         message += f"❓ {keyword} (Error fetching data)\n\n"

            await update.message.reply_text(message.strip())
            self.logger.info("Watchlist displayed successfully")

        except Exception as e:
            self.logger.error(f"Failed to list keywords: {str(e)}")
            await update.message.reply_text(f"Failed to retrieve watchlist: {str(e)}")

    async def get_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get the current portfolio"""
        try:
            portfolio_list = self.db.get_symbols()
            # Create a formatted message with stock data for each keyword
            message = "📊 Your Portfolio:\n\n"
            # show the symbols in the portfolio with /chart <symbol> command
            for portfolio in portfolio_list:
                message += f"- {portfolio.ticker} ({portfolio.quantity} shares)\n"
            message += f"\nTotal: {len(portfolio_list)} items"
            await update.message.reply_text(message.strip())
            self.logger.info("Portfolio displayed successfully")
        except Exception as e:
            self.logger.error(f"Failed to get portfolio: {str(e)}")
            await update.message.reply_text(f"Failed to retrieve portfolio: {str(e)}")

    async def check_alerts(self, context: ContextTypes.DEFAULT_TYPE):
        chat_id = context.application.bot_data.get("chat_id", 140283060)
        if not chat_id:
            self.logger.error("No chat ID configured")
            return

        try:
            portfolio_list = self.db.get_symbols()
            for portfolio in portfolio_list:
                await self._process_stock_alert(context, portfolio.ticker, chat_id)
        except Exception as e:
            self.logger.error(f"Error checking alerts: {str(e)}")

    async def _process_stock_alert(self, context, symbol: str, chat_id: str):
        try:
            # 오늘 알림 발송 내역이 있으면 무시
            if self.db.check_duplicate_alert(symbol):
                self.logger.info(f"Duplicate alert for {symbol}")
                return

            df = self.stock_service.get_stock_data(symbol, "1mo")
            if df.empty:
                return

            # RSI를 이용해서 매수/매도 신호 표시
            await self._process_rsi_alert(context, symbol, df, chat_id)

            # MACD 시그널를 이용한 매수/매도 신호 표시
            # self._process_macd_alert(context, symbol, df, chat_id)
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error processing {symbol}: {str(e)}")

    # RSI 시그널을 이용해서 매수/매도 판단
    async def _process_rsi_alert(
        self, context, symbol: str, df: pd.DataFrame, chat_id: str
    ):
        rsi = self.stock_service.calculate_rsi(df)

        # Buy/Sell signals based on RSI thresholds
        buy_signals = rsi < 30
        sell_signals = rsi > 70

        # 가장 최근 buy_signal이 True일 때만 alert 발송
        if buy_signals.iloc[-1]:
            await self._send_alert(
                context, symbol, "BUY", df["Close"].iloc[-1], chat_id
            )
        elif sell_signals.iloc[-1]:
            await self._send_alert(
                context, symbol, "SELL", df["Close"].iloc[-1], chat_id
            )

    # MACD 시그널을 이용해서 매수/매도 판단
    async def _process_macd_alert(
        self, context, symbol: str, df: pd.DataFrame, chat_id: str
    ):
        macd, signal = self.stock_service.calculate_macd(df)
        current_price = df["Adj Close"].iloc[-1]

        if self._is_buy_signal(macd, signal):
            await self._send_alert(context, symbol, "BUY", current_price, chat_id)
        elif self._is_sell_signal(macd, signal):
            await self._send_alert(context, symbol, "SELL", current_price, chat_id)

    async def _send_alert(
        self, context, symbol: str, action: str, price: float, chat_id: str
    ):
        """
        알림 메시지 발송

        Parameters:
        - context: ContextTypes.DEFAULT_TYPE
            - context에서 bot과 chat_id를 가져옵니다.
        - symbol: 심볼
        - alert_type: 알림 타입
        - price: 현재가격
        - chart: 차트 URL
        """
        self.logger.info(f"🔔 {symbol} 종목 {action} 알림 발송 시작")

        # 메시지 생성
        message = f"🚨 {symbol} {action} 신호 발생!\n현재가: ${price:.2f}"

        # 알림 기록 저장
        self.db.add_alert(symbol, action, price)
        self.logger.info(f"💾 {symbol} 종목 알림 기록 저장 완료")

        # 차트 생성
        chart = self.stock_service.generate_rsi_chart(
            symbol, self.stock_service.get_stock_data(symbol)
        )

        # 차트와 함께 메시지 발송
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=chart, caption=message)
            self.logger.info(f"✅ {symbol} 종목 {action} 알림 발송 완료")
        except Exception as e:
            self.logger.error(f"❌ {symbol} 종목 알림 발송 실패: {str(e)}")

    async def check_news(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Periodically check news for watched keywords and send alerts
        """
        chat_id = context.application.bot_data.get("chat_id", 140283060)
        if not chat_id:
            self.logger.error("No chat ID configured")
            return

        try:
            keywords = [keyword.keyword for keyword in self.db.get_watched_keywords()]
            if not keywords:
                self.logger.info("No keywords in watchlist")
                return

            for keyword in keywords:
                await self._process_news_alert(context, keyword, chat_id)

        except Exception as e:
            self.logger.error(f"Error checking news: {str(e)}")

    async def _process_news_alert(self, context, keyword: str, chat_id: str):
        """
        Process news alerts for a specific keyword

        Args:
            context: Telegram context
            keyword: Stock symbol or company name to check
            chat_id: Telegram chat ID for sending alerts
        """
        try:
            self.logger.info(f"Checking news for {keyword}")
            news_items = await self.news_service.get_news(keyword)

            if not news_items:
                self.logger.info(f"No news found for {keyword}")
                return

            # Get only the latest 3 news items
            latest_news = news_items[:3]
            self.logger.info(f"Sending {len(latest_news)} news items for {keyword}")

            for item in latest_news:
                news_message = self._format_news_message(keyword, item)
                await context.bot.send_message(
                    chat_id=chat_id, text=news_message, disable_web_page_preview=False
                )

            self.logger.info(f"Successfully sent news alerts for {keyword}")

        except Exception as e:
            self.logger.error(f"Error processing news for {keyword}: {str(e)}")

    def _format_news_message(self, keyword: str, news_item) -> str:
        """
        Format news item into a readable message

        Args:
            keyword: Stock symbol or company name
            news_item: News item object containing title, link, and published date

        Returns:
            str: Formatted message string
        """
        published_date = (
            news_item.published.strftime("%Y-%m-%d %H:%M")
            if hasattr(news_item, "published") and news_item.published
            else "Date not available"
        )

        return (
            f"📰 {keyword} News Alert\n\n"
            f"📌 {news_item.title}\n\n"
            f"🕒 {published_date}\n"
            f"🔗 {news_item.link}"
        )

    @staticmethod
    def _is_buy_signal(macd: pd.Series, signal: pd.Series) -> bool:
        return macd.iloc[-2] < signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1]

    @staticmethod
    def _is_sell_signal(macd: pd.Series, signal: pd.Series) -> bool:
        return macd.iloc[-2] > signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1]

    def run(self):
        app = ApplicationBuilder().token(self.settings.TELEGRAM_TOKEN).build()

        # Register handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("add", self.add_keyword))
        app.add_handler(CommandHandler("remove", self.remove_keyword))
        app.add_handler(CommandHandler("keywords", self.list_keywords))
        app.add_handler(CommandHandler("portfolio", self.get_portfolio))

        # Register jobs
        job_queue = app.job_queue
        job_queue.run_repeating(self.check_alerts, interval=600, first=3)  # 10 minutes
        job_queue.run_repeating(self.check_news, interval=3600, first=3)  # 1 hour

        app.run_polling(allowed_updates=Update.ALL_TYPES)
