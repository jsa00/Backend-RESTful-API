"""
인증 도메인 모델 (도메인 계층)

토큰을 다룰 때 계층 사이에 주고받는 값 객체를 정의한다.
복잡한 규칙 없이 데이터를 담아 전달하는 역할이라 같은 파일에 모아 두었다.
- TokenPayload: 검증을 통과한 JWT에서 꺼낸 정보
- BlacklistToken: 로그아웃으로 무효화된 토큰 정보
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TokenPayload:
    """검증된 토큰의 페이로드 (frozen=True라 만든 뒤 값을 바꿀 수 없음)"""

    user_id: UUID  # 토큰 주인 (JWT의 sub)
    jti: str  # 토큰 고유 ID (로그아웃 시 블랙리스트 키)
    exp: datetime  # 만료 시각


@dataclass
class BlacklistToken:
    """로그아웃된 토큰"""

    jti: str  # 무효화된 토큰 고유 ID
    expired_at: datetime  # 원래 만료 시각 (이 시각이 지나면 블랙리스트에서 지워도 된다.)
