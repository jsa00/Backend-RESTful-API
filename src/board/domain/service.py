"""
게시판 도메인 서비스 인터페이스 (도메인 계층)

비회원 글·댓글의 비밀번호를 해시하고 검증하는 인터페이스.
board 도메인이 user 도메인에 의존하지 않도록 user의 PasswordHasher와 별도로 둔다.
구현: infrastructure/security.py (bcrypt)
"""

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """비회원 비밀번호 해싱 인터페이스"""

    @abstractmethod
    def hash(self, raw_password: str) -> str:
        """평문 비밀번호를 단방향 해시값으로 변환"""

    @abstractmethod
    def verify(self, raw_password: str, hashed_password: str) -> bool:
        """평문 비밀번호와 해시값 일치 여부"""
