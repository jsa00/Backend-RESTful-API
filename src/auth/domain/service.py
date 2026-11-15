"""
인증 도메인 서비스 인터페이스 (도메인 계층)

토큰 발급·검증(pyjwt)과 회원 비밀번호 확인(user 도메인)은 외부 기술·다른 도메인이 필요하므로
"무엇을 하는지"만 추상 메서드로 정의하고 구현은 인프라 계층에 둔다.
- TokenProvider: JWT 발급·해독 (구현: infrastructure/security.py)
- UserCredentialVerifier: 이메일·비밀번호 확인 (구현: infrastructure/credentials_verifier.py)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from auth.domain.entities import TokenPayload


class TokenProvider(ABC):
    """액세스 토큰 발급·검증 인터페이스"""

    @abstractmethod
    def create_access_token(self, user_id: UUID) -> tuple[str, str, datetime, int]:
        """(token, jti, expired_at, expires_in_seconds) 반환"""

    @abstractmethod
    def decode_token(self, token: str) -> TokenPayload:
        """서명·만료 검증 후 페이로드 추출 (실패 시 UnauthorizedException)"""


class UserCredentialVerifier(ABC):
    """로그인 자격 증명 확인 인터페이스"""

    @abstractmethod
    async def verify_credentials(self, email: str, plain_password: str) -> UUID | None:
        """이메일·비밀번호가 맞으면 user_id, 아니면 None"""
