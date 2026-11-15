"""
공통 예외 클래스

도메인·서비스 코드는 HTTP를 몰라도 되도록, 상황에 맞는 예외만 raise 한다.
각 예외는 HTTP 상태 코드(status_code)와 에러 코드(error_code)를 들고 있고,
exception_handlers.py가 이를 받아 APIResponse 형식의 응답으로 바꾼다.

| 예외                  | 상태 코드 | 사용하는 상황                    |
| BadRequestException   | 400       | 요청은 형식상 맞지만 처리할 수 없음 |
| UnauthorizedException | 401       | 로그인(토큰) 필요·토큰 오류        |
| ForbiddenException    | 403       | 로그인했지만 권한 없음             |
| NotFoundException     | 404       | 대상 리소스 없음                   |
| ConflictException     | 409       | 중복 등 현재 상태와 충돌           |
| ValidationException   | 422       | 도메인 규칙 위반 (필드별 오류 포함) |
"""

from typing import Generic, TypeVar
from fastapi import status

# errors 필드에 담을 세부 오류 데이터 타입
T = TypeVar("T")


class SharedException(Exception, Generic[T]):
    """모든 애플리케이션 예외의 공통 부모 클래스"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "BAD_REQUEST",
        errors: T | None = None,
    ):
        self.message = message  # 사용자에게 보여줄 메시지
        self.status_code = status_code  # HTTP 상태 코드
        self.error_code = error_code  # 클라이언트가 구분할 에러 코드
        self.errors: T | None = errors  # 세부 오류 내용
        super().__init__(message)


# 400 잘못된 요청
class BadRequestException(SharedException[T]):
    def __init__(
        self,
        message: str,
        error_code: str = "BAD_REQUEST",
        errors: T | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            errors=errors,
        )


# 401 인증 실패
class UnauthorizedException(SharedException[None]):
    def __init__(
        self,
        message: str = "인증되지 않은 사용자입니다.",
        error_code: str = "UNAUTHORIZED",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            errors=None,
        )


# 403 권한 없음
class ForbiddenException(SharedException[None]):
    def __init__(
        self,
        message: str = "리소스에 접근할 권한이 없습니다.",
        error_code: str = "FORBIDDEN",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            errors=None,
        )


# 404 리소스 없음
class NotFoundException(SharedException[None]):
    def __init__(
        self,
        message: str = "리소스를 찾을 수 없습니다.",
        error_code: str = "NOT_FOUND",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            errors=None,
        )


# 409 중복 충돌
class ConflictException(SharedException[None]):
    def __init__(
        self,
        message: str = "리소스가 이미 존재합니다.",
        error_code: str = "CONFLICT",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            errors=None,
        )


# 422 도메인 유효성 검사 실패 (필드별 오류 목록 포함)
# 예: field_errors={"password": ["비밀번호는 8자 이상..."]}
class ValidationException(SharedException[dict[str, list[str]]]):
    def __init__(
        self,
        message: str = "유효성 검사에 실패했습니다.",
        error_code: str = "VALIDATION_ERROR",
        field_errors: dict[str, list[str]] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code=error_code,
            errors=field_errors or {},
        )
