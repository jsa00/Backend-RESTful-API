"""
로그인 자격 증명 확인 구현체 (인프라 계층)

auth 도메인의 UserCredentialVerifier 인터페이스를 user 도메인의 저장소·해셔로 구현한다.
auth 도메인이 user 도메인의 내부(User 엔티티 등)를 직접 다루지 않도록 이 클래스가 중간에서 연결한다.
"""

from uuid import UUID
from auth.domain.service import UserCredentialVerifier
from user.domain.repository import UserRepository
from user.domain.service import PasswordHasher


class UserCredentialVerifierImpl(UserCredentialVerifier):
    """회원 저장소 기반 UserCredentialVerifier 구현체"""

    def __init__(self, user_repo: UserRepository, password_hasher: PasswordHasher):
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    async def verify_credentials(self, email: str, plain_password: str) -> UUID | None:
        # 1) 이메일로 회원 조회
        user = await self._user_repo.find_by_email(email)
        if not user:
            return None

        # 2) 탈퇴한 회원은 로그인 불가
        #    다른 실패와 같은 응답을 주기 위해 None으로 돌려준다.
        if user.resign:
            return None

        # 3) 비밀번호 해시 비교
        if not self._password_hasher.verify(plain_password, user.password_hash):
            return None

        return user.id
