from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """현재 UTC 시각"""
    return datetime.now(timezone.utc)


# 모든 테이블 모델의 베이스 클래스
class Base(DeclarativeBase):
    pass


# 생성·수정·삭제 시각 공통 컬럼 (Mixin)
# default/onupdate에 함수(utc_now)를 넘겨야 INSERT/UPDATE 때마다 새 시각이 들어간다.
class DateTimeBase:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, onupdate=utc_now, nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )


def init_models() -> None:
    """SQLAlchemy 모델 메타데이터 등록"""
    # 도메인 모델을 만들면 여기서 import 해야 create_all 대상에 포함된다.
    # import user.infrastructure.models
    # import auth.infrastructure.models
    # import board.infrastructure.sqlalchemy.models
    pass
