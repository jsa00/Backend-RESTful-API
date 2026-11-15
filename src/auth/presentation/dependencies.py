"""
인증 의존성 (표현 계층)

- provide_auth_service: AuthService 주입 자리 (wiring/auth.py에서 연결)
- get_bearer_token / require_bearer_token: Authorization 헤더에서 토큰 문자열을 꺼내는 의존성
    bearer_scheme(shared/core/security.py)이 auto_error=False라 토큰이 없으면 None이 들어오고,
    직접 UnauthorizedException을 내서 401도 공통 응답 형식으로 나간다.
    (auto_error=True면 FastAPI가 {"detail": ...} 형식의 에러를 직접 반환한다.)
"""

from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from auth.application.service import AuthService
from shared.core.exceptions import UnauthorizedException
from shared.core.security import bearer_scheme


def provide_auth_service() -> AuthService:
    """AuthService 주입 자리 (wiring/auth.py에서 연결)"""
    raise NotImplementedError("AuthService 의존성이 주입되지 않았습니다.")


async def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str | None:
    """Bearer 토큰 문자열 (헤더가 없으면 None)"""
    return credentials.credentials if credentials else None


async def require_bearer_token(
    token: Annotated[str | None, Depends(get_bearer_token)],
) -> str:
    """Bearer 토큰 문자열 (헤더가 없으면 401)"""
    if token is None:
        raise UnauthorizedException(
            message="인증 토큰이 필요합니다.",
            error_code="TOKEN_REQUIRED",
        )
    return token
