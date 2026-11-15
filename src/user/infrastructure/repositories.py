"""
회원 저장소 구현체 (인프라 계층)

도메인의 UserRepository 인터페이스를 SQLAlchemy로 실제 구현한다.
- 조회: SELECT 결과(UserModel)를 to_user()로 도메인 엔티티로 바꿔 반환한다.
- 저장: id가 없으면 INSERT, 있으면 기존 행을 찾아 UPDATE 한다.
- DB 전용 에러(IntegrityError)는 여기서 공통 예외(ConflictException)로 바꿔,
    위 계층이 SQLAlchemy를 몰라도 되게 한다.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from shared.core.exceptions import ConflictException
from user.domain.repository import UserRepository
from user.domain.user import User
from user.infrastructure.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy 기반 UserRepository 구현체"""

    def __init__(self, session: AsyncSession):
        # 요청마다 get_db가 만든 세션을 받아 같은 트랜잭션 안에서 작업한다.
        self.session = session

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        user_model = await self.session.scalar(stmt)
        return user_model.to_user() if user_model else None

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        user_model = await self.session.scalar(stmt)
        return user_model.to_user() if user_model else None

    async def save(self, user: User) -> User:
        if user.id is None:
            # 신규 회원 등록(INSERT)
            user_model = UserModel(
                email=user.email,
                name=user.name,
                password_hash=user.password_hash,
                role=user.role,
                resign=user.resign,
            )
            self.session.add(user_model)
            try:
                # flush: 커밋 전에 INSERT를 DB로 보내 id·created_at을 받아온다.
                await self.session.flush()
            except IntegrityError as err:
                # 중복 확인과 저장 사이에 같은 이메일이 먼저 저장된 경우 unique 제약에 걸린다.
                raise ConflictException(
                    message="이미 사용 중인 이메일입니다.",
                    error_code="EMAIL_ALREADY_EXISTS",
                ) from err
            # refresh: DB가 채운 값(id, created_at)을 객체에 다시 읽어 온다.
            await self.session.refresh(user_model)
            return user_model.to_user()

        # 기존 회원 정보 수정(UPDATE)
        stmt = select(UserModel).where(UserModel.id == user.id)
        user_model = await self.session.scalar(stmt)
        if user_model is None:
            return user

        # 엔티티에서 바뀔 수 있는 값을 ORM 모델에 옮긴다.
        # modified_at은 DateTimeBase의 onupdate가 UPDATE 때 자동으로 기록한다.
        user_model.name = user.name
        user_model.password_hash = user.password_hash
        user_model.role = user.role
        user_model.resign = user.resign
        user_model.deleted_at = user.deleted_at

        await self.session.flush()
        await self.session.refresh(user_model)
        return user_model.to_user()
