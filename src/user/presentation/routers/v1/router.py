"""
회원 API 라우터 (표현 계층, /v1/users)

HTTP 요청을 받아 스키마로 검증하고 → UserService를 호출하고 → APIResponse로 감싸 반환한다.
비즈니스 로직은 넣지 않고, 요청·응답 변환만 담당한다.

| 메서드 | 경로                    | 기능          | 인증          |
| POST   | /v1/users               | 회원가입      | 불필요        |
| GET    | /v1/users/me            | 내 정보 조회  | 로그인 필요   |
| PATCH  | /v1/users/me/password   | 비밀번호 변경 | 로그인 필요   |
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status

from shared.core.openapi import AUTH_ERRORS, VALIDATION_ERRORS, error_responses
from shared.core.schemas import APIResponse
from user.application.service import UserService
from user.domain.user import User
from user.presentation.dependencies import get_current_user, provide_user_service
from user.presentation.schemas import ChangePasswordRequest, SignUpUserRequest, UserResponse

# prefix: 이 라우터의 모든 경로 앞에 붙는 주소 / tags: Swagger에서 묶이는 그룹 이름
router = APIRouter(prefix="/v1/users", tags=["Users"])


@router.post(
    "",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    responses=error_responses({409: ["EMAIL_ALREADY_EXISTS"]}, VALIDATION_ERRORS),
    description="이메일·이름·비밀번호로 새 회원을 등록합니다. 가입한 회원의 권한은 USER입니다.",
)
async def sign_up(
    request: SignUpUserRequest,
    user_service: Annotated[UserService, Depends(provide_user_service)],
):
    # request: 바디 JSON이 SignUpUserRequest로 검증된 뒤 들어온다.
    # user_service: wiring에서 연결한 실제 UserService가 주입된다.
    user = await user_service.register_user(
        email=request.email,
        name=request.name,
        password=request.password,
    )
    # 도메인 엔티티를 응답 스키마로 변환한다. (password_hash는 빠진다.)
    return APIResponse.ok(
        data=UserResponse.model_validate(user),
        message="회원가입이 완료되었습니다.",
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="내 정보 조회",
    responses=error_responses(AUTH_ERRORS),
    description="액세스 토큰의 주인인 로그인 회원 정보를 조회합니다.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    # 토큰 검증·회원 조회는 get_current_user가 끝낸 상태라 그대로 응답한다.
    return APIResponse.ok(data=UserResponse.model_validate(current_user))


@router.patch(
    "/me/password",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="비밀번호 변경",
    responses=error_responses({400: ["INVALID_OLD_PASSWORD", "SAME_PASSWORD"]}, AUTH_ERRORS, VALIDATION_ERRORS),
    description="로그인한 회원 본인의 비밀번호를 변경합니다. 현재 비밀번호 확인이 필요합니다.",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(provide_user_service)],
):
    # current_user: 토큰에서 찾아낸 로그인 회원 (wiring/auth.py에서 연결)
    # 경로에 user_id를 받지 않고 토큰의 회원 본인으로만 처리한다.
    await user_service.change_password(
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password,
    )
    return APIResponse.ok(message="비밀번호가 성공적으로 변경되었습니다.")
