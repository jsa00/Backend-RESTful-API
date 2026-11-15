"""
인증 요청·응답 스키마 (표현 계층)

- LoginRequest: 로그인 요청 바디 검증
- TokenResponse: 발급한 액세스 토큰 정보 (APIResponse의 data에 담겨 나간다.)
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""

    email: EmailStr = Field(
        description="로그인할 회원의 이메일",
        examples=["user@example.com"],
    )
    # 형식 검사는 하지 않고 비어 있는지만 본다. (형식 정보를 노출하지 않기 위해)
    password: str = Field(
        min_length=1,
        max_length=72,
        description="로그인할 회원의 비밀번호",
        examples=["P@ssw0rd!"],
    )


class TokenResponse(BaseModel):
    """액세스 토큰 응답 스키마"""

    access_token: str = Field(
        description="Authorization 헤더에 `Bearer {토큰}`으로 전달할 JWT 액세스 토큰 (HS512 서명)",
        examples=["eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi..."],
    )
    token_type: str = Field(
        default="bearer",
        description="토큰 인증 방식",
        examples=["bearer"],
    )
    expires_in: int = Field(
        description="액세스 토큰 유효 기간(초)",
        examples=[3600],
    )
