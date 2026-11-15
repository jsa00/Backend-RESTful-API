"""
인증 응용 서비스 (응용 계층)

로그인·로그아웃·토큰 검증 유스케이스를 처리한다.
의존 대상은 모두 인터페이스라서 pyjwt·SQLAlchemy·bcrypt를 직접 모른다.
- login: 이메일·비밀번호 확인 → 액세스 토큰 발급
- logout: 유효한 토큰인지 확인 → 블랙리스트 등록 → 만료된 블랙리스트 정리
- authenticate_token: 서명·만료 검증 + 블랙리스트 확인 (로그인 사용자 확인 의존성에서 사용)
"""

from datetime import datetime, timezone
from auth.domain.entities import TokenPayload
from auth.domain.repository import TokenBlacklistRepository
from auth.domain.service import TokenProvider, UserCredentialVerifier
from shared.core.exceptions import UnauthorizedException


class AuthService:
    """인증 응용 서비스"""

    def __init__(
        self,
        credential_verifier: UserCredentialVerifier,
        token_blacklist_repo: TokenBlacklistRepository,
        token_provider: TokenProvider,
    ):
        # 구현체는 wiring/auth.py에서 만들어 넣어준다.
        self._credential_verifier = credential_verifier
        self._blacklist_repo = token_blacklist_repo
        self._token_provider = token_provider

    async def login(self, email: str, plain_password: str) -> tuple[str, str, int]:
        """로그인 후 (access_token, token_type, expires_in) 반환"""
        user_id = await self._credential_verifier.verify_credentials(email, plain_password)
        if not user_id:
            # 이메일이 없는지 비밀번호가 틀렸는지 구분하지 않는다. (가입 여부 노출 방지)
            raise UnauthorizedException(
                message="이메일 또는 비밀번호가 올바르지 않습니다.",
                error_code="INVALID_CREDENTIALS",
            )

        token, _, _, expires_in = self._token_provider.create_access_token(user_id)
        return token, "bearer", expires_in

    async def logout(self, token: str) -> None:
        """로그아웃 (토큰을 블랙리스트에 등록해 남은 유효기간 동안 사용 차단)"""
        # 위조·만료·이미 로그아웃된 토큰이면 여기서 401이 난다.
        payload = await self.authenticate_token(token)
        await self._blacklist_repo.add(jti=payload.jti, expired_at=payload.exp)

        # 원래 만료 시각이 지난 블랙리스트는 어차피 쓸 수 없는 토큰이라 함께 정리한다.
        now = datetime.now(timezone.utc)
        await self._blacklist_repo.cleanup_expired(now)

    async def authenticate_token(self, token: str) -> TokenPayload:
        """토큰 검증 (서명·만료 + 블랙리스트)"""
        payload = self._token_provider.decode_token(token)
        if await self._blacklist_repo.is_blacklisted(payload.jti):
            raise UnauthorizedException(
                message="로그아웃된 토큰입니다.",
                error_code="TOKEN_REVOKED",
            )
        return payload
