"""
공통 로거 설정

- 앱 전체 로그 포맷과 레벨을 한 곳에서 정한다.
- 각 모듈은 get_logger(__name__)으로 자기 이름의 로거를 받아 쓴다.
- 로그 레벨은 .env의 LOGGING_MODE(debug / info)로 바꿀 수 있다.
"""

import os
import logging
from dotenv import load_dotenv

# .env 파일의 값을 환경변수로 불러온다.
load_dotenv()

# LOGGING_MODE=debug 이면 DEBUG, 그 외에는 INFO 레벨
log_mode = os.getenv("LOGGING_MODE", "info").lower()
log_level = logging.DEBUG if log_mode == "debug" else logging.INFO

# 로그 한 줄 형식: 시각 [레벨] 로거이름 (파일:줄번호) - 메시지
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 루트 로거 설정
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


# 이름을 따로 지정하지 않고 쓸 때의 기본 로거
logger = get_logger()
