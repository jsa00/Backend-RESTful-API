"""
회원 엔티티 (도메인 계층)

회원 데이터와 회원에 관한 비즈니스 규칙을 한 곳에 모은 순수 파이썬 클래스.
DB·HTTP·bcrypt 같은 외부 기술을 직접 알지 않고, 해싱은 PasswordHasher 인터페이스에 맡긴다.

회원 도메인 규칙
1. 비밀번호는 8자 이상 72자 이하이며 영문, 숫자, 특수문자(@$!%*#?&)를 모두 포함해야 한다.
    (bcrypt는 72바이트를 넘는 비밀번호를 처리하지 못한다.)
2. 이메일은 유효한 형식이어야 하며 로그인에 사용되므로 중복될 수 없다.
3. 이름은 2자 이상 20자 이하여야 한다.
4. 탈퇴는 소프트 삭제로 처리하며 deleted_at에 탈퇴 시각을 기록하고 resign을 True로 바꾼다.
5. 탈퇴는 본인 또는 관리자만 처리할 수 있다.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from shared.core.exceptions import BadRequestException, ForbiddenException, ValidationException
from user.domain.service import PasswordHasher

# 이메일 형식: 아이디@도메인.최상위도메인
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# 비밀번호 형식
# (?=.*[A-Za-z]) 영문 1개 이상 / (?=.*\d) 숫자 1개 이상 / (?=.*[@$!%*#?&]) 특수문자 1개 이상
# [A-Za-z\d@$!%*#?&]{8,72} 허용 문자만으로 8~72자
PASSWORD_REGEX = re.compile(
    r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,72}$"
)

# 회원 권한 (일반 회원 / 관리자)
Role = Literal["USER", "ADMIN"]


@dataclass
class User:
    """회원 엔티티"""

    email: str  # 로그인 아이디로 쓰는 이메일
    name: str  # 이름
    password_hash: str  # 해시된 비밀번호 (평문은 저장하지 않음)
    role: Role  # 권한
    resign: bool  # 탈퇴 여부

    # 기본값이 있는 필드는 아래쪽에 둬야 한다.
    # 아래 값은 DB에 저장된 뒤 채워진다. (신규 생성 시에는 None)
    id: uuid.UUID | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self):
        # 객체가 만들어질 때마다(신규 생성·DB 조회 모두) 이메일·이름 규칙을 검사한다.
        self._validate_email(self.email)
        self._validate_name(self.name)

    @classmethod
    def create(
        cls,
        email: str,
        name: str,
        raw_password: str,
        hasher: PasswordHasher,
        role: Role = "USER",
    ) -> "User":
        """신규 회원 생성 (비밀번호 규칙 검증 후 해시 저장)"""
        # 평문 비밀번호는 여기서만 검사하고, 엔티티에는 해시값만 남긴다.
        cls._validate_password(raw_password)
        password_hash = hasher.hash(raw_password)

        return cls(
            email=email,
            name=name,
            password_hash=password_hash,
            role=role,
            resign=False,
        )

    def change_password(
        self,
        old_password: str,
        new_password: str,
        hasher: PasswordHasher,
    ) -> None:
        """비밀번호 변경"""
        # 1) 탈퇴한 회원은 변경 불가
        if self.resign:
            raise ForbiddenException(
                message="탈퇴한 회원은 비밀번호를 변경할 수 없습니다.",
                error_code="USER_ALREADY_WITHDRAWN",
            )

        # 2) 기존 비밀번호 일치 여부 확인
        if not hasher.verify(old_password, self.password_hash):
            raise BadRequestException(
                message="기존 비밀번호가 일치하지 않습니다.",
                error_code="INVALID_OLD_PASSWORD",
            )

        # 3) 동일 비밀번호로 변경 방지
        if old_password == new_password:
            raise BadRequestException(
                message="새 비밀번호는 이전 비밀번호와 동일할 수 없습니다.",
                error_code="SAME_PASSWORD",
            )

        # 4) 새 비밀번호 규칙 검증
        self._validate_password(new_password)

        # 5) 새 해시로 교체하고 수정 시각을 기록한다.
        self.password_hash = hasher.hash(new_password)
        self.modified_at = datetime.now(timezone.utc)

    def withdraw(self, requester: "User") -> None:
        """회원 탈퇴 (소프트 삭제)"""
        # requester: 탈퇴를 요청한 사람 (본인 또는 관리자)
        if self.resign:
            raise BadRequestException(
                message="이미 탈퇴 처리된 사용자입니다.",
                error_code="ALREADY_WITHDRAWN",
            )

        # 본인이거나 관리자일 때만 허용
        is_owner = self.id is not None and self.id == requester.id
        is_admin = requester.role == "ADMIN"
        if not (is_owner or is_admin):
            raise ForbiddenException(
                message="탈퇴 처리는 본인 또는 관리자 권한만 가능합니다.",
                error_code="WITHDRAW_PERMISSION_DENIED",
            )

        # 행을 지우지 않고 탈퇴 표시만 남긴다. (소프트 삭제)
        now = datetime.now(timezone.utc)
        self.resign = True
        self.deleted_at = now
        self.modified_at = now

    def grant_admin(self) -> None:
        """관리자 권한 부여 (서버 관리 스크립트 전용, API로는 노출하지 않음)"""
        if self.resign:
            raise BadRequestException(
                message="탈퇴한 회원은 관리자로 지정할 수 없습니다.",
                error_code="USER_ALREADY_WITHDRAWN",
            )
        if self.role == "ADMIN":
            raise BadRequestException(
                message="이미 관리자인 회원입니다.",
                error_code="ALREADY_ADMIN",
            )
        self.role = "ADMIN"
        self.modified_at = datetime.now(timezone.utc)

    # 규칙 검증 메서드
    # 규칙을 어기면 필드별 오류를 담은 ValidationException(422)을 발생시킨다.

    @staticmethod
    def _validate_email(email: str) -> None:
        if not EMAIL_REGEX.match(email):
            raise ValidationException(
                message="유효하지 않은 이메일 형식입니다.",
                field_errors={"email": ["올바른 이메일 형식을 입력하세요."]},
            )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not (2 <= len(name) <= 20):
            raise ValidationException(
                message="이름은 2자 이상 20자 이하여야 합니다.",
                field_errors={"name": ["이름 길이는 2자 이상 20자 이하여야 합니다."]},
            )

    @staticmethod
    def _validate_password(raw_password: str) -> None:
        if not PASSWORD_REGEX.match(raw_password):
            raise ValidationException(
                message="비밀번호 제약 조건을 만족하지 못했습니다.",
                field_errors={
                    "password": [
                        "비밀번호는 8자 이상 72자 이하이며 영문, 숫자, 특수문자(@$!%*#?&)를 포함해야 합니다."
                    ]
                },
            )
