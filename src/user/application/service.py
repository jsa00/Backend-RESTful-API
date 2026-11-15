"""
회원 응용 서비스 (응용 계층)

라우터에서 받은 요청을 하나의 "유스케이스"로 처리하는 곳.
저장소에서 회원을 꺼내고 → 엔티티의 규칙 메서드를 호출하고 → 다시 저장하는 흐름을 조립한다.
비즈니스 규칙 자체(비밀번호 형식 등)는 User 엔티티에 있고, 여기서는 순서만 담당한다.
의존 대상은 모두 인터페이스(UserRepository, PasswordHasher)라서 DB·bcrypt를 직접 모른다.
"""

import uuid
from shared.core.exceptions import ConflictException, NotFoundException
from user.domain.repository import UserRepository
from user.domain.service import PasswordHasher
from user.domain.user import User


class UserService:
    """회원 응용 서비스"""

    def __init__(self, repository: UserRepository, hasher: PasswordHasher):
        # 구현체는 wiring/user.py에서 만들어 넣어준다.
        self.repository = repository
        self.hasher = hasher

    async def register_user(self, email: str, name: str, password: str) -> User:
        """회원가입"""
        # 1) 이메일 중복 확인
        if await self.repository.find_by_email(email):
            raise ConflictException(
                message="이미 사용 중인 이메일입니다.",
                error_code="EMAIL_ALREADY_EXISTS",
            )

        # 2) 엔티티 생성 시 이메일·이름·비밀번호 규칙을 검증한다.
        #    규칙 위반은 ValidationException(422)이 그대로 전달된다.
        user = User.create(
            email=email,
            name=name,
            raw_password=password,
            hasher=self.hasher,
        )
        # 3) 저장 후 id·created_at이 채워진 엔티티를 돌려준다.
        return await self.repository.save(user)

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
    ) -> None:
        """비밀번호 변경"""
        # 1) 대상 회원 조회
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundException(
                message="사용자를 찾을 수 없습니다.",
                error_code="USER_NOT_FOUND",
            )

        # 2) 엔티티가 기존 비밀번호 확인·규칙 검증·해시 교체를 처리한다.
        user.change_password(
            old_password=old_password,
            new_password=new_password,
            hasher=self.hasher,
        )
        # 3) 바뀐 해시를 DB에 반영한다. (커밋은 요청이 끝날 때 get_db가 한다.)
        await self.repository.save(user)
