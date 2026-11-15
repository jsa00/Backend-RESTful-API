"""
회원 저장소 인터페이스 (도메인 계층)

회원을 "어디에, 어떻게" 저장하는지는 모르고 "무엇을 할 수 있는지"만 정의한다.
응용 서비스(UserService)는 이 인터페이스만 보고 코드를 쓰고,
실제 DB 처리는 infrastructure/repositories.py의 SqlAlchemyUserRepository가 담당한다.
메서드는 ORM 모델이 아닌 도메인 엔티티(User)를 주고받는다.
"""

import uuid
from abc import ABC, abstractmethod
from user.domain.user import User


class UserRepository(ABC):
    """회원 저장소 인터페이스 (구현은 인프라 계층)"""

    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """ID 기준 회원 단건 조회"""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """이메일 기준 회원 단건 조회"""

    @abstractmethod
    async def save(self, user: User) -> User:
        """신규 생성(INSERT) 또는 변경 사항 반영(UPDATE)"""
