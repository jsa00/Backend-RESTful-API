"""
회원 ORM 모델 (인프라 계층)

users 테이블의 컬럼 구조를 SQLAlchemy로 정의한다.
도메인 엔티티(User)와 DB 테이블을 분리해 두었기 때문에,
DB에서 꺼낸 UserModel은 to_user()로 도메인 엔티티로 바꿔서 위 계층에 넘긴다.
"""

import uuid
from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from shared.core.models import Base, DateTimeBase
from user.domain.user import User


class UserModel(Base, DateTimeBase):
    """users 테이블 ORM 모델 (DateTimeBase로 created_at·modified_at·deleted_at 포함)"""

    __tablename__ = "users"

    # 기본키 (UUID, INSERT 때 자동 생성)
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 이메일 (unique 제약 + 조회용 인덱스)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # 이름
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    # bcrypt 해시 비밀번호 (60자)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 권한 (USER / ADMIN)
    role: Mapped[str] = mapped_column(String(20), default="USER", nullable=False)
    # 탈퇴 여부
    resign: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def to_user(self) -> User:
        """ORM 모델 -> 도메인 엔티티 변환"""
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            password_hash=self.password_hash,
            role=self.role,
            resign=self.resign,
            created_at=self.created_at,
            modified_at=self.modified_at,
            deleted_at=self.deleted_at,
        )
