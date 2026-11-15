"""
애플리케이션 진입점

FastAPI 앱을 만들고 공통 설정을 한 곳에서 조립한다.
- lifespan: 서버 시작 시 모델 등록·테이블 생성, 종료 시 커넥션 풀 정리
- register_exception_handlers: 모든 에러를 APIResponse 형식으로 응답
- wire_dependencies: placeholder 의존성에 실제 구현체 연결
- include_router: 도메인별 API 경로 등록

실행: uv run uvicorn main:app --app-dir src --reload
문서: http://localhost:8000/docs (Swagger UI)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from wiring import wire_dependencies
from shared.core.database import close_db, engine
from shared.core.exception_handlers import register_exception_handlers
from shared.core.logger import get_logger
from shared.core.models import Base, init_models
from user.presentation.routers.v1.router import router as user_router

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델 등록·테이블 생성, 종료 시 커넥션 풀 정리"""
    # yield 이전: 서버가 요청을 받기 전에 한 번 실행된다.
    logger.info("애플리케이션 시작, 모델 초기화 및 DB 스키마 확인 중...")
    init_models()

    # 등록된 모델 중 DB에 없는 테이블만 생성한다. (이미 있는 테이블은 건드리지 않는다.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("애플리케이션 준비 완료.")
    yield

    # yield 이후: 서버가 종료될 때 한 번 실행된다.
    logger.info("애플리케이션 종료 처리 중...")
    await close_db()


# title·description·version은 Swagger 문서 상단에 표시된다.
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

# 라우터 등록
app.include_router(user_router)
