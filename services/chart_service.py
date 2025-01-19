import yfinance as yf
import matplotlib.pyplot as plt
import io


def moving_average(df, column, window=20):
    """이동평균을 계산하는 함수"""
    return df[column].rolling(window=window).mean()


def exponential_moving_average(df, column, span):
    """지수이동평균을 계산하는 함수"""
    return df[column].ewm(span=span, adjust=False).mean()


def calculate_macd(df):
    """MACD 계산"""
    # MACD 지수이동평균선 (Exponential Moving Average)
    # 12일과 26일의 EMA를 사용하여 MACD 지수이동평균선을 계산
    exp1 = exponential_moving_average(df, "Close", 12)
    exp2 = exponential_moving_average(df, "Close", 26)

    # MACD 신호선 (Signal Line)
    macd = exp1 - exp2
    # Signal Line은 MACD의 EMA로, 9일을 사용하여 계산
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def calculate_rsi(data, window=14):
    """RSI 계산 함수"""
    delta = data["Close"].diff(1)  # 종가의 변화량을 계산
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()  # 상승률 계산
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()  # 하락률 계산

    rs = gain / loss  # RS(Relative Strength) 계산
    rsi = 100 - (100 / (1 + rs))  # RSI 계산
    return rsi


def generate_price_chart(symbol, chart_data):
    """차트 생성"""
    macd, signal = calculate_macd(chart_data)

    plt.figure(figsize=(12, 6))

    plt.subplot(2, 1, 1)
    plt.plot(chart_data.index, chart_data["Close"], label="Close Price")
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


def generate_macd_signal_chart(symbol, chart_data):
    """차트 생성"""
    # Moving Average Convergence Divergence (MACD) indicator를 이용한 매수/매도 신호 계산
    macd, signal = calculate_macd(chart_data)
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(chart_data.index, chart_data["Close"], label="Close Price")

    # Buy and sell signals
    buy_signals = (macd > signal)[signal.first_valid_index() :]
    sell_signals = ~(macd > signal)[signal.first_valid_index()]

    if any(buy_signals):
        plt.scatter(
            chart_data.index[buy_signals],
            chart_data["Close"][buy_signals],
            marker="^",
            color="green",
            label="Buy Signal",
        )
    if any(sell_signals):
        plt.scatter(
            chart_data.index[sell_signals],
            chart_data["Close"][sell_signals],
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


def generate_rsi_chart(symbol, chart_data, rsi_window=14):
    """RSI를 이용한 매수/매도 신호 표시 차트 생성"""
    rsi = calculate_rsi(chart_data, window=rsi_window)
    chart_data["RSI"] = rsi

    # Buy/Sell signals based on RSI thresholds
    buy_signals = rsi < 30
    sell_signals = rsi > 70

    # Plotting
    plt.figure(figsize=(12, 8))

    # Plot close price
    plt.subplot(2, 1, 1)
    plt.plot(chart_data.index, chart_data["Close"], label="Close Price", color="blue")

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
