"""
인증 의존성 조립 (Composition Root)

1) auth 도메인의 placeholder(provide_auth_service)에 실제 AuthService를 연결한다.
2) user 도메인에 자리만 만들어 둔 로그인 사용자 확인 의존성을 여기서 연결한다.
    - get_optional_user: 토큰이 없으면 None(비회원), 있으면 검증 후 회원
    - get_current_user: 토큰 필수, 없으면 401
    - require_admin: 로그인 + ADMIN 권한, 아니면 403

import 방향이 wiring.auth → wiring.user 한쪽이라 순환 import가 생기지 않는다.
FastAPI는 한 요청 안에서 같은 의존성(get_db 등)을 한 번만 실행하고 결과를 재사용하므로,
AuthService와 UserRepository는 같은 DB 세션을 공유한다.
"""

import uuid
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from auth.application.service import AuthService
from auth.domain.repository import TokenBlacklistRepository
from auth.domain.service import TokenProvider
from auth.infrastructure.credentials_verifier import UserCredentialVerifierImpl
from auth.infrastructure.repositories import SqlAlchemyTokenBlacklistRepository
from auth.infrastructure.security import JwtTokenProvider
from auth.presentation.dependencies import get_bearer_token, provide_auth_service
from shared.core.database import get_db
from shared.core.exceptions import ForbiddenException, UnauthorizedException
from user.domain.repository import UserRepository
from user.domain.user import User
from user.presentation.dependencies import get_current_user, get_optional_user, require_admin
from wiring.user import create_user_repository, password_hasher

# 서버 시작 시 한 번 생성 (JWT_SECRET_KEY가 없으면 여기서 RuntimeError로 시작이 중단된다.)
token_provider: TokenProvider = JwtTokenProvider.from_env()


def create_token_blacklist_repository(
    session: AsyncSession = Depends(get_db),
) -> TokenBlacklistRepository:
    """요청마다 DB 세션을 받아 블랙리스트 저장소 구현체 생성"""
    return SqlAlchemyTokenBlacklistRepository(session)


def create_auth_service(
    user_repository: UserRepository = Depends(create_user_repository),
    blacklist_repository: TokenBlacklistRepository = Depends(create_token_blacklist_repository),
) -> AuthService:
    """자격 증명 확인기·블랙리스트 저장소·토큰 발급기를 넣어 인증 서비스 생성"""
    return AuthService(
        credential_verifier=UserCredentialVerifierImpl(
            user_repo=user_repository,
            password_hasher=password_hasher,
        ),
        token_blacklist_repo=blacklist_repository,
        token_provider=token_provider,
    )


async def resolve_optional_user(
    token: Annotated[str | None, Depends(get_bearer_token)],
    auth_service: Annotated[AuthService, Depends(create_auth_service)],
    user_repo: Annotated[UserRepository, Depends(create_user_repository)],
) -> User | None:
    """토큰이 없으면 None, 있으면 검증 후 회원 반환 (위조·만료·로그아웃 토큰은 401)"""
    if token is None:
        return None

    # 1) 서명·만료·블랙리스트 검증
    payload = await auth_service.authenticate_token(token)

    # 2) 토큰 주인 조회
    user = await user_repo.find_by_id(uuid.UUID(str(payload.user_id)))
    if not user:
        raise UnauthorizedException(
            message="존재하지 않는 사용자입니다.",
            error_code="USER_NOT_FOUND",
        )

    # 3) 탈퇴 회원은 토큰이 남아 있어도 이용 불가
    if user.resign:
        raise ForbiddenException(
            message="탈퇴한 회원은 서비스를 이용할 수 없습니다.",
            error_code="USER_ALREADY_WITHDRAWN",
        )
    return user


async def resolve_current_user(
    current_user: Annotated[User | None, Depends(resolve_optional_user)],
) -> User:
    """로그인 필수 (토큰이 없으면 401)"""
    if current_user is None:
        raise UnauthorizedException(
            message="인증 토큰이 필요합니다.",
            error_code="TOKEN_REQUIRED",
        )
    return current_user


async def resolve_require_admin(
    current_user: Annotated[User, Depends(resolve_current_user)],
) -> User:
    """관리자 필수 (일반 회원이면 403)"""
    if current_user.role != "ADMIN":
        raise ForbiddenException(
            message="관리자 권한이 필요합니다.",
            error_code="ADMIN_PERMISSION_DENIED",
        )
    return current_user


def wire_auth_dependencies(app: FastAPI) -> None:
    """인증 의존성 + 로그인 사용자 확인 의존성 바인딩"""
    app.dependency_overrides.update(
        {
            provide_auth_service: create_auth_service,
            get_optional_user: resolve_optional_user,
            get_current_user: resolve_current_user,
            require_admin: resolve_require_admin,
        }
    )
