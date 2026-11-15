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

# 데이터베이스 접속 정보
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

# 커넥션 풀 설정 및 비동기 엔진
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
# expire_on_commit=False: 커밋 후에도 객체 속성이 남아 있어 비동기 지연 로딩(MissingGreenlet) 에러가 나지 않는다.
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
            yield session
            await session.commit()
        except Exception:
            await session.rollback()  # 오류가 나면 작업을 모두 취소한다.
            raise


async def close_db() -> None:
    """서버 종료 시 커넥션 풀 반환"""
    logger.info("데이터베이스 엔진 연결 풀을 종료합니다.")
    await engine.dispose()
