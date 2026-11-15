"""
헬스체크 API

배포 스크립트·Docker 헬스체크·외부 모니터링에서 서버 상태를 확인할 때 쓴다.
- 앱이 응답하고 DB에 SELECT 1이 성공하면 200
- DB에 접속할 수 없으면 503 (APIResponse 형식, 원인은 로그에만 남김)
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from shared.core.database import engine
from shared.core.logger import get_logger
from shared.core.schemas import APIResponse, ErrorResponse

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=APIResponse[dict[str, str]],
    summary="헬스체크",
    description="서버와 데이터베이스 연결 상태를 확인합니다.",
    responses={503: {"model": ErrorResponse, "description": "데이터베이스 연결 실패 — code: `SERVICE_UNAVAILABLE`"}},
)
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("헬스체크 실패: 데이터베이스에 연결할 수 없습니다.")
        response_dto = APIResponse.fail(
            code="SERVICE_UNAVAILABLE",
            message="데이터베이스에 연결할 수 없습니다.",
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_dto.model_dump(mode="json"),
        )
    return APIResponse.ok(data={"status": "ok", "database": "ok"})
