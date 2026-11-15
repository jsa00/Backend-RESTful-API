"""
회원 의존성 조립 (Composition Root)

user/presentation/dependencies.py의 placeholder 자리에 실제 구현체를 끼워 넣는다.
요청이 들어오면 FastAPI가 아래 순서로 객체를 만들어 라우터에 넘긴다.
    get_db → AsyncSession
        → create_user_repository → SqlAlchemyUserRepository(session)
            → create_user_service → UserService(repository, password_hasher)
인프라 구현체를 import 하는 곳은 이 파일뿐이라, 구현을 바꿀 때 여기만 고치면 된다.
"""

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.database import get_db
from user.application.service import UserService
from user.domain.repository import UserRepository
from user.domain.service import PasswordHasher
from user.infrastructure.repositories import SqlAlchemyUserRepository
from user.infrastructure.security import BcryptPasswordHasher
from user.presentation.dependencies import provide_user_repository, provide_user_service

# 상태가 없는 구현체라 앱 전체에서 하나만 사용
password_hasher: PasswordHasher = BcryptPasswordHasher()


def create_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """요청마다 DB 세션을 받아 회원 저장소 구현체 생성"""
    return SqlAlchemyUserRepository(session)


def create_user_service(
    repository: UserRepository = Depends(create_user_repository),
) -> UserService:
    """저장소·해셔를 넣어 회원 응용 서비스 생성"""
    return UserService(repository=repository, hasher=password_hasher)


def wire_user_dependencies(app: FastAPI) -> None:
    """회원 의존성 바인딩"""
    # dependency_overrides[자리] = 실제 함수
    # 라우터가 Depends(provide_user_service)를 쓰면 create_user_service가 대신 실행된다.
    # get_current_user·get_optional_user·require_admin은 토큰 검증이 필요해 Auth 단계에서 연결한다.
    app.dependency_overrides.update(
        {
            provide_user_repository: create_user_repository,
            provide_user_service: create_user_service,
        }
    )
