"""
회원 요청·응답 스키마 (표현 계층)

Pydantic 모델로 HTTP 요청 바디를 검증하고 응답 JSON의 모양을 정한다.
- 요청 스키마: Field의 min_length 등 제약을 어기면 FastAPI가 자동으로 422를 반환한다.
- 응답 스키마: 내보낼 필드만 정의해서 password_hash 같은 민감 정보가 응답에 섞이지 않게 한다.
- description·examples는 Swagger 문서에 그대로 표시된다.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignUpUserRequest(BaseModel):
    """회원가입 요청 스키마"""

    # EmailStr: 이메일 형식이 아니면 422
    email: EmailStr = Field(
        description="로그인에 사용할 사용자 이메일",
        examples=["user@example.com"],
    )
    name: str = Field(
        min_length=2,
        max_length=20,
        description="사용자 이름 (2~20자)",
        examples=["홍길동"],
    )
    # 길이는 여기서 먼저 막고, 영문·숫자·특수문자 조합은 도메인(User)에서 검사한다.
    password: str = Field(
        min_length=8,
        max_length=72,
        description="비밀번호 (8~72자, 영문/숫자/특수문자 @$!%*#?& 포함)",
        examples=["P@ssw0rd!"],
    )


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청 스키마"""

    old_password: str = Field(
        min_length=1,
        description="현재 비밀번호",
        examples=["P@ssw0rd!"],
    )
    new_password: str = Field(
        min_length=8,
        max_length=72,
        description="새 비밀번호 (8~72자, 영문/숫자/특수문자 @$!%*#?& 포함)",
        examples=["N3wP@ssw0rd!"],
    )


class UserResponse(BaseModel):
    """회원 정보 응답 스키마 (비밀번호 해시는 포함하지 않음)"""

    # from_attributes=True: 도메인 엔티티처럼 속성(user.email)으로 접근하는 객체도 변환할 수 있다.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="회원 식별 ID")
    email: str = Field(description="이메일")
    name: str = Field(description="이름")
    role: str = Field(description="권한 (USER, ADMIN)")
    created_at: datetime | None = Field(None, description="가입 일시(UTC)")
