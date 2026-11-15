"""
회원 의존성 주입 명세 (표현 계층)

라우터가 Depends(...)로 받을 대상을 "자리(placeholder)"로만 선언한다.
함수 본문은 NotImplementedError뿐이고, 실제 구현은 wiring/user.py·wiring/auth.py에서
app.dependency_overrides로 바꿔 끼운다.
→ 표현 계층(라우터)이 인프라 구현체(SqlAlchemy, bcrypt)를 직접 import 하지 않게 된다.
→ 연결되지 않은 채 호출되면 NotImplementedError가 나서 500으로 응답한다.

로그인 사용자 확인 placeholder에는 bearer_scheme 의존성을 선언해 둔다.
Swagger 문서는 실제 실행 함수가 아니라 라우터에 선언된 placeholder를 보고 만들어지므로,
여기에 선언해야 해당 API에 자물쇠가 붙고 "Try it out"이 토큰을 헤더에 실어 보낸다.
"""

from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from shared.core.security import bearer_scheme
from user.application.service import UserService
from user.domain.repository import UserRepository
from user.domain.user import User

# 주입 명세(placeholder)
# 실제 구현체는 wiring에서 app.dependency_overrides로 바인딩한다.

# Swagger 문서용 토큰 선언 (값은 쓰지 않음)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def provide_user_service() -> UserService:
    """UserService 주입 자리 (wiring/user.py에서 연결)"""
    raise NotImplementedError("UserService 의존성이 주입되지 않았습니다.")


def provide_user_repository() -> UserRepository:
    """UserRepository 주입 자리 (wiring/user.py에서 연결)"""
    raise NotImplementedError("UserRepository 의존성이 주입되지 않았습니다.")


async def get_current_user(_: BearerCredentials) -> User:
    """로그인 사용자 (토큰 필수, wiring/auth.py에서 연결)"""
    raise NotImplementedError("get_current_user 의존성이 주입되지 않았습니다.")


async def get_optional_user(_: BearerCredentials) -> User | None:
    """로그인 사용자 또는 비회원(None) (wiring/auth.py에서 연결)"""
    raise NotImplementedError("get_optional_user 의존성이 주입되지 않았습니다.")


async def require_admin(_: BearerCredentials) -> User:
    """관리자 사용자 (wiring/auth.py에서 연결)"""
    raise NotImplementedError("require_admin 의존성이 주입되지 않았습니다.")
