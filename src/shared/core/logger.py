import os
import logging
from dotenv import load_dotenv

load_dotenv()

# LOGGING_MODE=debug 이면 DEBUG, 그 외에는 INFO 레벨
log_mode = os.getenv("LOGGING_MODE", "info").lower()
log_level = logging.DEBUG if log_mode == "debug" else logging.INFO

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# force=True: uvicorn 등이 먼저 설정한 로거도 우리 포맷·레벨로 덮어쓴다.
logging.basicConfig(
    level=log_level,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    force=True,
)


def get_logger(name: str | None = None) -> logging.Logger:
    """이름별 로거 반환 (이름이 없으면 LOGGER_NAME 환경변수 사용)"""
    logger_name = name or os.getenv("LOGGER_NAME", "app")
    return logging.getLogger(logger_name)


logger = get_logger()
