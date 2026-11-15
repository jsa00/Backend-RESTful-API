"""
회원 의존성 주입 명세 (표현 계층)

라우터가 Depends(...)로 받을 대상을 "자리(placeholder)"로만 선언한다.
함수 본문은 NotImplementedError뿐이고, 실제 구현은 wiring/user.py에서
app.dependency_overrides로 바꿔 끼운다.
→ 표현 계층(라우터)이 인프라 구현체(SqlAlchemy, bcrypt)를 직접 import 하지 않게 된다.
→ 연결되지 않은 채 호출되면 NotImplementedError가 나서 500으로 응답한다.
"""

from user.application.service import UserService
from user.domain.repository import UserRepository
from user.domain.user import User

# 주입 명세(placeholder)
# 실제 구현체는 wiring에서 app.dependency_overrides로 바인딩한다.


def provide_user_service() -> UserService:
    """UserService 주입 자리 (wiring/user.py에서 연결)"""
    raise NotImplementedError("UserService 의존성이 주입되지 않았습니다.")


def provide_user_repository() -> UserRepository:
    """UserRepository 주입 자리 (wiring/user.py에서 연결)"""
    raise NotImplementedError("UserRepository 의존성이 주입되지 않았습니다.")


async def get_current_user() -> User:
    """로그인 사용자 (토큰 필수, Auth 단계에서 연결)"""
    raise NotImplementedError("get_current_user 의존성이 주입되지 않았습니다.")


async def get_optional_user() -> User | None:
    """로그인 사용자 또는 비회원(None) (Auth 단계에서 연결)"""
    raise NotImplementedError("get_optional_user 의존성이 주입되지 않았습니다.")


async def require_admin() -> User:
    """관리자 사용자 (Auth 단계에서 연결)"""
    raise NotImplementedError("require_admin 의존성이 주입되지 않았습니다.")
