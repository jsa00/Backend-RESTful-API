from contextlib import asynccontextmanager
from fastapi import FastAPI
from wiring import wire_dependencies
from shared.core.database import close_db, engine
from shared.core.exception_handlers import register_exception_handlers
from shared.core.logger import get_logger
from shared.core.models import Base, init_models

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델 등록·테이블 생성, 종료 시 커넥션 풀 정리"""
    logger.info("애플리케이션 시작, 모델 초기화 및 DB 스키마 확인 중...")
    init_models()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("애플리케이션 준비 완료.")
    yield

    logger.info("애플리케이션 종료 처리 중...")
    await close_db()


app = FastAPI(
    title="게시판 API",
    description="JWT 인증·인가를 적용한 RESTful 게시판 백엔드 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 전역 예외 핸들러 바인딩
register_exception_handlers(app)

# 의존성 주입 일괄 바인딩
wire_dependencies(app)
