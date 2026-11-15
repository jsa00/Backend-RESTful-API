"""
토큰 블랙리스트 ORM 모델 (인프라 계층)

token_blacklist 테이블 구조를 정의한다.
로그아웃된 토큰의 jti와 원래 만료 시각만 저장하면 충분하다.
"""

from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.models import Base


class TokenBlacklistModel(Base):
    """token_blacklist 테이블 ORM 모델"""

    __tablename__ = "token_blacklist"

    # 토큰 고유 ID (uuid4 문자열 36자, 기본키라 조회가 빠르다.)
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 원래 만료 시각 (정리 작업에서 범위 조회하므로 인덱스)
    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
