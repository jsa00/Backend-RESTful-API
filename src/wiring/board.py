"""
게시판 의존성 조립 (Composition Root)

1) 게시판 저장소·서비스 placeholder에 실제 구현체를 연결한다.
2) 로그인 사용자(user 도메인)를 게시판 권한 등급(Role)으로 바꿔 board 도메인에 넘긴다.
    - get_current_role: get_optional_user 결과 → None(비회원) / Role.USER / Role.ADMIN
    - require_admin_role: require_admin 재사용 → 비로그인 401, 일반 회원 403, 관리자면 Role.ADMIN
board 도메인 코드는 User 엔티티를 모르고, user ↔ board 연결은 이 파일에서만 한다.
"""

from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from board.application.service import BoardService
from board.domain.enums import Role
from board.domain.repository.board_repository import BoardRepository
from board.infrastructure.sqlalchemy.board_repository import SqlAlchemyBoardRepository
from board.presentation.dependencies import (
    get_current_role,
    provide_board_repository,
    provide_board_service,
    require_admin_role,
)
from shared.core.database import get_db
from user.domain.user import User
from user.presentation.dependencies import get_optional_user, require_admin


def create_board_repository(session: AsyncSession = Depends(get_db)) -> BoardRepository:
    """요청마다 DB 세션을 받아 게시판 저장소 구현체 생성"""
    return SqlAlchemyBoardRepository(session)


def create_board_service(
    board_repo: BoardRepository = Depends(create_board_repository),
) -> BoardService:
    """게시판 설정 서비스 생성"""
    return BoardService(board_repo=board_repo)


async def resolve_current_role(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> Role | None:
    """로그인 사용자 → 게시판 권한 등급 (비회원 None)"""
    if user is None:
        return None
    return Role(user.role)


async def resolve_require_admin_role(
    _: Annotated[User, Depends(require_admin)],
) -> Role:
    """관리자 확인 (require_admin이 401/403 처리)"""
    return Role.ADMIN


def wire_board_dependencies(app: FastAPI) -> None:
    """게시판 의존성 바인딩"""
    app.dependency_overrides.update(
        {
            provide_board_repository: create_board_repository,
            provide_board_service: create_board_service,
            get_current_role: resolve_current_role,
            require_admin_role: resolve_require_admin_role,
        }
    )
