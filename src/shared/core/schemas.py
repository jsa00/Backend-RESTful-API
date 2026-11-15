"""
공통 응답 스키마

모든 API가 같은 모양으로 응답하도록 감싸는 APIResponse를 정의한다.
- 성공: APIResponse.ok(data=...)    → success=True, code="OK", data에 결과
- 실패: APIResponse.fail(message=...) → success=False, code=에러 코드, errors에 세부 내용
Generic[T]라서 APIResponse[UserResponse]처럼 data의 타입을 지정하면 Swagger 문서에도 그대로 표시된다.
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

# data 필드에 들어갈 응답 데이터 타입
T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """모든 API 공통 응답 형식"""

    success: bool = Field(description="처리 성공/실패 여부")
    code: str | None = Field(
        None, description="비즈니스 식별 코드 (성공 시 OK, 실패 시 에러 코드)"
    )
    message: str | None = Field(None, description="성공 또는 실패 시 설명")
    errors: dict[str, list[str]] | list[str] | Any | None = Field(
        None, description="실패 시 세부 오류 내용"
    )
    data: T | None = Field(None, description="성공 시 응답 데이터")
    responded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="응답 날짜시간(UTC)",
    )

    @classmethod
    def ok(
        cls,
        data: T | None = None,
        message: str = "요청이 성공적으로 처리되었습니다.",
        code: str = "OK",
    ) -> "APIResponse[T]":
        """성공 응답 생성"""
        return cls(
            success=True,
            code=code,
            message=message,
            errors=None,
            data=data,
        )

    @classmethod
    def fail(
        cls,
        message: str,
        code: str = "BAD_REQUEST",
        errors: dict[str, list[str]] | list[str] | Any | None = None,
    ) -> "APIResponse[None]":
        """실패 응답 생성 (전역 예외 처리기에서 사용)"""
        return cls(
            success=False,
            code=code,
            message=message,
            errors=errors,
            data=None,
        )
