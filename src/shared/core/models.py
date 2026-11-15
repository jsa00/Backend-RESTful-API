"""
ORM 모델 공통 베이스

- Base: 모든 테이블 모델이 상속하는 SQLAlchemy 기본 클래스
- DateTimeBase: created_at / modified_at / deleted_at 공통 컬럼 Mixin
- init_models: 서버 시작 시 모델 파일을 import 해 테이블 생성 대상에 등록한다.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """현재 UTC 시각"""
    return datetime.now(timezone.utc)


# 모든 테이블 모델의 베이스 클래스
# 이 클래스를 상속한 모델은 Base.metadata에 모여 create_all 때 테이블로 만들어진다.
class Base(DeclarativeBase):
    pass


# 생성·수정·삭제 시각 공통 컬럼 (Mixin)
# default/onupdate에 함수(utc_now)를 넘겨야 INSERT/UPDATE 때마다 새 시각이 들어간다.
class DateTimeBase:
    # 생성 시각 (INSERT 때 자동 기록)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    # 수정 시각 (UPDATE 때 자동 기록, 처음에는 비어 있음)
    modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, onupdate=utc_now, nullable=True
    )
    # 삭제 시각 (소프트 삭제용, 값이 있으면 삭제된 데이터)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )


def init_models() -> None:
    """SQLAlchemy 모델 메타데이터 등록"""
    # 도메인 모델을 만들면 여기서 import 해야 create_all 대상에 포함된다.
    import user.infrastructure.models  # noqa: F401  회원
    # import auth.infrastructure.models
    # import board.infrastructure.sqlalchemy.models
