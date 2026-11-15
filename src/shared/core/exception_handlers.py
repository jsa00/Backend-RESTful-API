"""
전역 예외 처리기

어디서 예외가 나든 여기서 가로채 APIResponse.fail 형식의 JSON 응답으로 바꾼다.
그래서 라우터·서비스에는 try/except 없이 예외만 raise 하면 된다.

| 처리 대상               | 상태 코드         | 응답 code                 |
| SharedException 계열    | 예외에 지정된 값  | 예외의 error_code         |
| RequestValidationError  | 422               | REQUEST_VALIDATION_ERROR  |
| 그 외 모든 Exception    | 500               | INTERNAL_SERVER_ERROR     |
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from shared.core.exceptions import SharedException
from shared.core.logger import get_logger
from shared.core.schemas import APIResponse

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """전역 예외 처리기 등록 (모든 에러를 APIResponse 형식으로 반환)"""

    # 비즈니스 예외 (SharedException 및 하위 도메인 예외)
    @app.exception_handler(SharedException)
    async def shared_exception_handler(request: Request, exc: SharedException):
        # 5xx는 서버 문제라 error, 4xx는 클라이언트 요청 문제라 warning으로 남긴다.
        if exc.status_code >= 500:
            logger.error("비즈니스 서버 오류 [%s]: %s", exc.error_code, exc.message)
        else:
            logger.warning(
                "클라이언트 요청 예외 [%s]: %s (path: %s, method: %s)",
                exc.error_code,
                exc.message,
                request.url.path,
                request.method,
            )

        # 예외가 들고 있는 코드·메시지·세부 오류를 그대로 응답에 담는다.
        response_dto = APIResponse.fail(
            code=exc.error_code,
            message=exc.message,
            errors=exc.errors,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response_dto.model_dump(mode="json"),
        )

    # Pydantic 스키마 검증 실패 (422)
    # 요청 바디·쿼리·경로 값이 스키마(Field 제약 등)에 맞지 않을 때 FastAPI가 발생시킨다.
    # loc 경로를 "field.subfield" 키로 묶어 { 필드: [메시지, ...] } 형태로 정규화한다.
    # 예: loc=("body", "password") → "password"
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors_map: dict[str, list[str]] = {}
        for err in exc.errors():
            loc = ".".join(str(item) for item in err["loc"] if item != "body")
            field_name = loc if loc else "non_field_errors"
            errors_map.setdefault(field_name, []).append(err["msg"])

        logger.warning(
            "요청 파라미터 유효성 검증 실패 (path: %s, method: %s): %s",
            request.url.path,
            request.method,
            errors_map,
        )

        response_dto = APIResponse.fail(
            code="REQUEST_VALIDATION_ERROR",
            message="요청 입력값 검증에 실패했습니다.",
            errors=errors_map,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=response_dto.model_dump(mode="json"),
        )

    # 처리되지 않은 시스템 내부 오류 (500)
    # 스택 트레이스는 로그에만 남기고, 응답에는 안내 메시지만 내려준다.
    # (내부 구현 정보가 클라이언트에 노출되지 않는다.)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "처리되지 않은 치명적 시스템 오류 발생 (path: %s, method: %s): %s",
            request.url.path,
            request.method,
            exc,
        )

        response_dto = APIResponse.fail(
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다. 관리자에게 문의해주세요.",
            errors=None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_dto.model_dump(mode="json"),
        )
