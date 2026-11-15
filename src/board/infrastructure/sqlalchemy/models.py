"""
게시판 ORM 모델 (인프라 계층)

- boards: 게시판 설정. 권한 5가지는 Role 값(ALL / USER / ADMIN)을 문자열로 저장한다.
- posts: 게시글. boards와 N:1, users와 N:1(비회원 글은 author_id가 NULL)
(댓글 comments 테이블은 2차에서 추가하며, 새 테이블이라 create_all이 자동으로 만든다.)
"""

import uuid
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
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


class PostModel(Base, DateTimeBase):
    """posts 테이블 ORM 모델"""

    __tablename__ = "posts"
    __table_args__ = (
        # 게시판별 목록 조회(삭제 안 된 글, 최신순)에 쓰는 인덱스
        Index("ix_posts_board_id_deleted_at_id", "board_id", "deleted_at", "id"),
        Index("ix_posts_author_id", "author_id"),
    )

    # 게시글 번호 (자동 증가)
    post_id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=True)
    board_id: Mapped[str] = mapped_column(String(30), ForeignKey("boards.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 작성자 (회원은 author_id + 가입 이름, 비회원은 author_id NULL + 닉네임)
    author_name: Mapped[str] = mapped_column(String(20), nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # 비회원 비밀번호 bcrypt 해시 (회원 글은 NULL)
    guest_password: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # 조회수
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    # 게시판 이름을 함께 쓰기 위해 조회할 때 boards를 JOIN으로 같이 가져온다. (추가 쿼리 없음)
    board: Mapped[BoardModel] = relationship(lazy="joined")
