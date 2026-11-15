"""
토큰 블랙리스트 저장소 인터페이스 (도메인 계층)

JWT는 서버에 저장하지 않는 토큰이라, 만료 전에 무효화하려면 "이 토큰은 쓰면 안 된다"는 목록이 필요하다.
로그아웃하면 토큰의 jti를 블랙리스트에 넣고, 인증할 때마다 목록에 있는지 확인한다.
토큰 자체는 회원 ID로 그때그때 만들기 때문에 토큰 저장소는 따로 두지 않는다.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class TokenBlacklistRepository(ABC):
    """토큰 블랙리스트 저장소 인터페이스 (구현은 인프라 계층)"""

    @abstractmethod
    async def add(self, jti: str, expired_at: datetime) -> None:
        """블랙리스트에 토큰 식별자 등록"""

    @abstractmethod
    async def is_blacklisted(self, jti: str) -> bool:
        """블랙리스트 등록 여부"""

    @abstractmethod
    async def cleanup_expired(self, current_time: datetime) -> int:
        """원래 만료 시각이 지난 항목 삭제 후 삭제 개수 반환"""
