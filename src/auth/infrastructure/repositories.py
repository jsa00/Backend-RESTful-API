"""
토큰 블랙리스트 저장소 구현체 (인프라 계층)

도메인의 TokenBlacklistRepository 인터페이스를 SQLAlchemy로 구현한다.
"""

from datetime import datetime
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.repository import TokenBlacklistRepository
from auth.infrastructure.models import TokenBlacklistModel


class SqlAlchemyTokenBlacklistRepository(TokenBlacklistRepository):
    """SQLAlchemy 기반 TokenBlacklistRepository 구현체"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, jti: str, expired_at: datetime) -> None:
        blacklist_item = TokenBlacklistModel(jti=jti, expired_at=expired_at)
        self.session.add(blacklist_item)
        await self.session.flush()

    async def is_blacklisted(self, jti: str) -> bool:
        # 행 전체가 아니라 jti 컬럼만 조회해 존재 여부만 확인한다.
        stmt = select(TokenBlacklistModel.jti).where(TokenBlacklistModel.jti == jti)
        result = await self.session.scalar(stmt)
        return result is not None

    async def cleanup_expired(self, current_time: datetime) -> int:
        # DELETE FROM token_blacklist WHERE expired_at <= 현재시각
        stmt = delete(TokenBlacklistModel).where(TokenBlacklistModel.expired_at <= current_time)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
