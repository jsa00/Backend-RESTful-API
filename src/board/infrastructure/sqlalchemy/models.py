"""
게시판 ORM 모델 (인프라 계층)

boards 테이블 구조를 정의한다. (게시글·댓글 테이블은 다음 단계에서 추가)
권한 5가지는 Role 값(ALL / USER / ADMIN)을 문자열로 저장한다.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from shared.core.models import Base, DateTimeBase


class BoardModel(Base, DateTimeBase):
    """boards 테이블 ORM 모델 (DateTimeBase로 created_at·modified_at·deleted_at 포함)"""

    __tablename__ = "boards"

    # 게시판 ID (DB 컬럼 이름은 id, 파이썬 속성 이름은 board_id)
    board_id: Mapped[str] = mapped_column("id", String(30), primary_key=True)
    board_name: Mapped[str] = mapped_column(String(50), nullable=False)
    page_size: Mapped[int] = mapped_column(Integer, default=20, nullable=False)

    # 게시판 권한 (Role 값 문자열)
    edit_role: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)
    view_role: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)
    list_role: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)
    comment_list_role: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)
    comment_edit_role: Mapped[str] = mapped_column(String(20), default="ALL", nullable=False)
