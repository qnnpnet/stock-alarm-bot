# 로거 생성 함수
from logging.handlers import TimedRotatingFileHandler
import logging
import os


def setup_logger():
    # 로그 디렉토리 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로거 설정
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # 로그 포맷 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 파일 핸들러 설정 (매일 자정에 새로운 파일 생성)
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "stock_bot.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
