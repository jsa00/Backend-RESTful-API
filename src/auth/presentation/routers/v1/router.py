"""
인증 API 라우터 (표현 계층, /v1/auth)

| 메서드 | 경로             | 기능                          | 인증        |
| POST   | /v1/auth/login   | 로그인 (액세스 토큰 발급)     | 불필요      |
| POST   | /v1/auth/logout  | 로그아웃 (토큰 블랙리스트)    | 토큰 필요   |
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status

from auth.application.service import AuthService
from auth.presentation.dependencies import provide_auth_service, require_bearer_token
from auth.presentation.schemas import LoginRequest, TokenResponse
from shared.core.openapi import VALIDATION_ERRORS, error_responses
from shared.core.schemas import APIResponse

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="로그인",
    responses=error_responses({401: ["INVALID_CREDENTIALS"]}, VALIDATION_ERRORS),
    description="이메일과 비밀번호를 확인하고 JWT 액세스 토큰(HS512)을 발급합니다.",
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(provide_auth_service)],
):
    token, token_type, expires_in = await auth_service.login(request.email, request.password)
    return APIResponse.ok(
        data=TokenResponse(
            access_token=token,
            token_type=token_type,
            expires_in=expires_in,
        ),
        message="로그인되었습니다.",
    )


@router.post(
    "/logout",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="로그아웃",
    responses=error_responses({401: ["TOKEN_REQUIRED", "INVALID_TOKEN", "TOKEN_EXPIRED", "TOKEN_REVOKED"]}),
    description="현재 액세스 토큰을 블랙리스트에 등록해 남은 유효기간 동안 사용할 수 없게 합니다.",
)
async def logout(
    token: Annotated[str, Depends(require_bearer_token)],
    auth_service: Annotated[AuthService, Depends(provide_auth_service)],
):
    await auth_service.logout(token)
    return APIResponse.ok(message="로그아웃되었습니다.")
