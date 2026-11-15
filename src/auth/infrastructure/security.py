"""
JWT 토큰 구현체 (인프라 계층)

도메인의 TokenProvider 인터페이스를 PyJWT로 구현한다.
- 서명 알고리즘: HS512 (같은 시크릿 키로 서명하고 검증하는 대칭키 방식)
- 페이로드: sub(회원 ID), jti(토큰 고유 ID), iat(발급 시각), exp(만료 시각)
- 설정값은 .env에서 읽는다.
    JWT_SECRET_KEY: 서명 키 (필수, `openssl rand -hex 64`로 생성)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 액세스 토큰 유효 시간(분, 기본 60)
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from auth.domain.entities import TokenPayload
from auth.domain.service import TokenProvider
from shared.core.exceptions import UnauthorizedException
from shared.core.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# HS512 권장 키 길이 (512비트 = 64바이트)
RECOMMENDED_SECRET_BYTES = 64


class JwtTokenProvider(TokenProvider):
    """PyJWT 기반 TokenProvider 구현체"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS512",
        access_token_expire_minutes: int = 60,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = access_token_expire_minutes

    @classmethod
    def from_env(cls) -> "JwtTokenProvider":
        """환경변수로 생성 (시크릿 키가 없으면 서버 시작을 막음)"""
        secret_key = os.getenv("JWT_SECRET_KEY", "").strip()
        if not secret_key:
            # 기본 키를 코드에 두면 저장소가 공개됐을 때 누구나 토큰을 위조할 수 있다.
            raise RuntimeError(
                "JWT_SECRET_KEY 환경변수가 없습니다. `openssl rand -hex 64` 값을 .env에 설정하세요."
            )
        if len(secret_key.encode("utf-8")) < RECOMMENDED_SECRET_BYTES:
            logger.warning("JWT_SECRET_KEY가 %d바이트보다 짧습니다. 더 긴 키를 권장합니다.", RECOMMENDED_SECRET_BYTES)

        expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        return cls(secret_key=secret_key, access_token_expire_minutes=expire_minutes)

    def create_access_token(self, user_id: uuid.UUID) -> tuple[str, str, datetime, int]:
        now = datetime.now(timezone.utc)
        expires_delta = timedelta(minutes=self.expire_minutes)
        expired_at = now + expires_delta
        expires_in = int(expires_delta.total_seconds())
        jti = str(uuid.uuid4())  # 토큰마다 다른 고유 ID (로그아웃 시 이 값으로 차단)

        payload = {
            "sub": str(user_id),
            "jti": jti,
            "iat": now,
            "exp": expired_at,
        }
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt, jti, expired_at, expires_in

    def decode_token(self, token: str) -> TokenPayload:
        try:
            # 서명이 맞는지, exp가 지나지 않았는지, 필수 항목이 있는지 PyJWT가 검사한다.
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require": ["sub", "jti", "exp"]},
            )
            return TokenPayload(
                user_id=uuid.UUID(payload["sub"]),
                jti=payload["jti"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
        except jwt.ExpiredSignatureError as err:
            raise UnauthorizedException(
                message="만료된 토큰입니다. 다시 로그인해주세요.",
                error_code="TOKEN_EXPIRED",
            ) from err
        except (jwt.PyJWTError, KeyError, ValueError) as err:
            # 서명 불일치(위조), 형식 오류, sub가 UUID가 아닌 경우 등
            raise UnauthorizedException(
                message="유효하지 않은 토큰입니다.",
                error_code="INVALID_TOKEN",
            ) from err
