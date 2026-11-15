"""
데이터베이스 연결 설정 (SQLAlchemy 비동기 + asyncpg)

- engine: PostgreSQL과 연결을 맺고 커넥션 풀을 관리하는 객체
- AsyncSessionLocal: 요청마다 새 세션(작업 단위)을 만드는 팩토리
- get_db: FastAPI Depends로 요청 하나에 세션 하나를 빌려주고,
    요청이 끝나면 커밋(성공) 또는 롤백(실패)한 뒤 반납한다.
- close_db: 서버 종료 시 커넥션 풀을 정리한다.
"""

import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from shared.core.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# 데이터베이스 접속 정보 (형식: postgresql+asyncpg://사용자:비밀번호@호스트:포트/DB이름)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

# 커넥션 풀 설정 및 비동기 엔진
# - pool_size: 평소 유지하는 연결 수
# - max_overflow: 바쁠 때 추가로 더 만들 수 있는 연결 수
# - pool_timeout: 빈 연결을 기다리는 최대 시간(초)
# - pool_recycle: 오래된 연결을 30분마다 새로 교체한다.
# - pool_pre_ping: 연결을 꺼내기 전에 살아 있는지 먼저 확인한다.
# - echo: True면 실행되는 SQL을 로그로 출력한다.
POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("CONNECTION_POOL_MAX_SIZE", "20"))
engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=30.0,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
)

# 비동기 세션 팩토리
# - autoflush=False: 조회할 때마다 변경 사항을 자동으로 DB에 보내지 않고, flush를 직접 호출할 때만 보낸다.
# - expire_on_commit=False: 커밋 후에도 객체 속성이 남아 있어 비동기 지연 로딩(MissingGreenlet) 에러가 나지 않는다.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """요청 단위 DB 세션 제공 (정상 종료 시 커밋, 예외 시 롤백)"""
    async with AsyncSessionLocal() as session:
        try:
            # yield 시점에 라우터·서비스·저장소가 이 세션으로 작업한다.
            yield session
            # 요청 처리가 에러 없이 끝나면 한 번에 커밋한다.
            await session.commit()
        except Exception:
            await session.rollback()  # 오류가 나면 작업을 모두 취소한다.
            raise


async def close_db() -> None:
    """서버 종료 시 커넥션 풀 반환"""
    logger.info("데이터베이스 엔진 연결 풀을 종료합니다.")
    await engine.dispose()
