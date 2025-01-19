import traceback
import yfinance as yf
from typing import Tuple, Optional
import pandas as pd
import io
import numpy as np
import matplotlib.pyplot as plt
from utils.logger import setup_logger


class StockService:
    def __init__(self):
        self.logger = setup_logger()

    @staticmethod
    def get_stock_data(symbol: str, period: str = "3mo") -> pd.DataFrame:
        stock = yf.Ticker(symbol)
        return stock.history(period=period)

    @staticmethod
    def calculate_macd(data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        exp1 = data["Close"].ewm(span=12, adjust=False).mean()
        exp2 = data["Close"].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

    @staticmethod
    def calculate_rsi(data, window=14):
        """RSI 계산 함수"""
        delta = data["Close"].diff(1)  # 종가의 변화량을 계산
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()  # 상승률 계산
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()  # 하락률 계산

        rs = gain / loss  # RS(Relative Strength) 계산
        rsi = 100 - (100 / (1 + rs))  # RSI 계산
        return rsi

    def generate_price_chart(self, symbol: str, data: pd.DataFrame) -> io.BytesIO:
        """종가 차트 생성"""
        plt.figure(figsize=(10, 6))
        plt.plot(data.index, data["Close"])
        plt.title(f"{symbol} Stock Price")
        plt.xlabel("Date")
        plt.ylabel("Price")

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        return buf

    def generate_macd_signal_chart(
        self, symbol: str, chart_data: pd.DataFrame
    ) -> io.BytesIO:
        """MACD 시그널 차트 생성"""
        macd, signal = self.calculate_macd(chart_data)
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(chart_data.index, chart_data["Close"], label="Close Price")

        try:

            # Buy and sell signals
            # buy_signals = (macd > signal)[signal.first_valid_index() :]
            # sell_signals = ~buy_signals
            # 주가와 함께 확인
            price_above_ma = (
                chart_data["Close"] > chart_data["Close"].rolling(window=20).mean()
            )  # 20일 SMA
            buy_signals = (macd > signal) & price_above_ma
            sell_signals = (macd < signal) & ~price_above_ma

            if any(buy_signals):
                plt.scatter(
                    chart_data.index[
                        buy_signals
                    ],  # Use directly the index with boolean array
                    chart_data["Close"][
                        buy_signals
                    ],  # Use directly the column with boolean array
                    marker="^",
                    color="green",
                    label="Buy Signal",
                )
            if any(sell_signals):
                plt.scatter(
                    chart_data.index[
                        sell_signals
                    ],  # Use directly the index with boolean array
                    chart_data["Close"][
                        sell_signals
                    ],  # Use directly the column with boolean array
                    marker="v",
                    color="red",
                    label="Sell Signal",
                )

            plt.title(f"{symbol} Stock Price")
            plt.legend()
            plt.subplot(2, 1, 2)
            plt.plot(chart_data.index, macd, label="MACD")
            plt.plot(chart_data.index, signal, label="Signal")
            plt.legend()

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error generating chart: {str(e)}")
            return None

    def generate_rsi_chart(self, symbol, chart_data, rsi_window=14):
        """RSI를 이용한 매수/매도 신호 표시 차트 생성"""
        rsi = self.calculate_rsi(chart_data, window=rsi_window)
        chart_data["RSI"] = rsi

        # Buy/Sell signals based on RSI thresholds
        buy_signals = rsi < 30
        sell_signals = rsi > 70

        # Plotting
        plt.figure(figsize=(12, 8))

        # Plot close price
        plt.subplot(2, 1, 1)
        plt.plot(
            chart_data.index, chart_data["Close"], label="Close Price", color="blue"
        )

        if any(buy_signals):
            plt.scatter(
                chart_data.index[buy_signals],
                chart_data["Close"][buy_signals],
                marker="^",
                color="green",
                label="Buy Signal (RSI < 30)",
            )
        if any(sell_signals):
            plt.scatter(
                chart_data.index[sell_signals],
                chart_data["Close"][sell_signals],
                marker="v",
                color="red",
                label="Sell Signal (RSI > 70)",
            )

        plt.title(f"{symbol} Stock Price and RSI Signals")
        plt.legend()

        # Plot RSI
        plt.subplot(2, 1, 2)
        plt.plot(chart_data.index, rsi, label="RSI", color="purple")
        plt.axhline(30, color="green", linestyle="--", label="Oversold (30)")
        plt.axhline(70, color="red", linestyle="--", label="Overbought (70)")
        plt.fill_between(chart_data.index, 30, 70, color="gray", alpha=0.2)
        plt.title("RSI Indicator")
        plt.legend()

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return buf
