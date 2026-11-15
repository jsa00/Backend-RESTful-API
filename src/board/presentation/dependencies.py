"""
게시판 의존성 주입 명세 (표현 계층)

라우터가 Depends(...)로 받을 대상을 placeholder로만 선언하고, 실제 구현은 wiring/board.py에서 연결한다.
board 도메인은 user 도메인을 직접 알지 않고, 요청자를 게시판 권한 등급(Role)으로만 받는다.
    - 비로그인(비회원): None
    - 로그인 일반 회원: Role.USER
    - 관리자: Role.ADMIN
로그인 정보가 필요한 placeholder에는 BearerCredentials를 선언해 Swagger가 토큰을 보내게 한다.
게시글 작성자는 get_current_author로 받는다. (로그인 회원이면 Author.member, 비회원이면 None)
"""

from board.application.service import BoardService, PostService
from board.domain.enums import Role
from board.domain.post import Author
from board.domain.repository.board_repository import BoardRepository
from shared.core.security import BearerCredentials


def provide_board_repository() -> BoardRepository:
    """BoardRepository 주입 자리 (wiring/board.py에서 연결)"""
    raise NotImplementedError("BoardRepository 의존성이 주입되지 않았습니다.")


def provide_board_service() -> BoardService:
    """BoardService 주입 자리 (wiring/board.py에서 연결)"""
    raise NotImplementedError("BoardService 의존성이 주입되지 않았습니다.")


def provide_post_service() -> PostService:
    """PostService 주입 자리 (wiring/board.py에서 연결)"""
    raise NotImplementedError("PostService 의존성이 주입되지 않았습니다.")


async def get_current_author(_: BearerCredentials) -> Author | None:
    """로그인 회원을 작성자로 변환 (비회원 None)"""
    raise NotImplementedError("get_current_author 의존성이 주입되지 않았습니다.")


async def get_current_role(_: BearerCredentials) -> Role | None:
    """요청자 권한 등급 (비회원 None, 회원 USER, 관리자 ADMIN)"""
    raise NotImplementedError("get_current_role 의존성이 주입되지 않았습니다.")


async def require_admin_role(_: BearerCredentials) -> Role:
    """관리자 권한 확인 (비로그인 401, 일반 회원 403)"""
    raise NotImplementedError("require_admin_role 의존성이 주입되지 않았습니다.")
