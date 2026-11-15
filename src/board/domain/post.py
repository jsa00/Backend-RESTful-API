"""
게시글 엔티티와 값 객체 (도메인 계층)

게시글 규칙
1. 게시판 권한(edit_role)을 만족해야 글을 쓰고 고치고 지울 수 있다. (확인은 PostService에서)
2. 회원 글은 작성자 본인 또는 관리자만 수정·삭제할 수 있다.
3. 비회원 글은 작성할 때 6~72자 비밀번호를 등록해야 하고,
    수정·삭제할 때 그 비밀번호가 맞아야 한다. (관리자는 비밀번호 없이 가능)
4. 제목은 1~200자, 본문은 1~10,000자이며 공백만으로는 쓸 수 없다.
5. 게시글은 소프트 삭제하며, 삭제된 글은 수정할 수 없다.

값 객체 (frozen=True라 만든 뒤 값을 바꿀 수 없음)
- BoardInfo: 글이 속한 게시판 ID·이름
- Author: 작성자 (author_id가 None이면 비회원)
- GuestPassword: 비회원 비밀번호 해시
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from board.domain.enums import Role
from board.domain.service import PasswordHasher
from shared.core.exceptions import BadRequestException, ValidationException

TITLE_MAX = 200
CONTENT_MAX = 10_000
AUTHOR_NAME_MAX = 20
GUEST_PASSWORD_MIN = 6
GUEST_PASSWORD_MAX = 72  # bcrypt는 72바이트를 넘는 비밀번호를 처리하지 못한다.


@dataclass(frozen=True)
class BoardInfo:
    """게시판 정보 값 객체"""

    board_id: str
    board_name: str


@dataclass(frozen=True)
class Author:
    """작성자 값 객체"""

    author_name: str  # 화면에 보이는 작성자 이름 (회원은 가입 이름, 비회원은 입력한 닉네임)
    author_id: uuid.UUID | None = None  # None이면 비회원

    def __post_init__(self):
        name = (self.author_name or "").strip()
        if not (1 <= len(name) <= AUTHOR_NAME_MAX):
            raise ValidationException(
                message="작성자 정보 유효성 검사에 실패했습니다.",
                field_errors={"author_name": [f"작성자 이름은 1~{AUTHOR_NAME_MAX}자여야 합니다."]},
            )

    @property
    def is_guest(self) -> bool:
        """비회원 여부"""
        return self.author_id is None

    @classmethod
    def member(cls, user_id: uuid.UUID, username: str) -> "Author":
        """회원 작성자"""
        return cls(author_id=user_id, author_name=username.strip())

    @classmethod
    def guest(cls, guest_name: str) -> "Author":
        """비회원 작성자"""
        return cls(author_id=None, author_name=(guest_name or "").strip())

    def is_owner(self, user_id: uuid.UUID | None) -> bool:
        """요청자가 작성자 본인인지 여부 (비회원 글은 항상 False)"""
        if self.is_guest or user_id is None:
            return False
        return self.author_id == user_id


@dataclass(frozen=True)
class GuestPassword:
    """비회원 비밀번호 값 객체 (평문은 보관하지 않고 해시값만 가짐)"""

    hashed_value: str

    @classmethod
    def create(cls, raw_password: str, hasher: PasswordHasher) -> "GuestPassword":
        """평문 길이 검증 후 해시"""
        if not raw_password or not (GUEST_PASSWORD_MIN <= len(raw_password) <= GUEST_PASSWORD_MAX):
            raise ValidationException(
                message="비회원 비밀번호 유효성 검사에 실패했습니다.",
                field_errors={
                    "guest_password": [
                        f"비회원 비밀번호는 {GUEST_PASSWORD_MIN}~{GUEST_PASSWORD_MAX}자여야 합니다."
                    ]
                },
            )
        return cls(hashed_value=hasher.hash(raw_password))

    def verify(self, raw_password: str | None, hasher: PasswordHasher) -> bool:
        if not raw_password or len(raw_password) > GUEST_PASSWORD_MAX:
            return False
        return hasher.verify(raw_password, self.hashed_value)


@dataclass
class Post:
    """게시글 엔티티"""

    board_info: BoardInfo
    title: str
    content: str
    author: Author
    guest_password: GuestPassword | None = None
    view_count: int = 0
    post_id: int | None = None  # DB 저장 후 채워지는 게시글 번호

    created_at: datetime | None = None
    modified_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self):
        field_errors = self._collect_content_errors(self.title, self.content)
        if self.author.is_guest and self.guest_password is None:
            field_errors.setdefault("guest_password", []).append("비회원 글은 비밀번호가 필요합니다.")
        if field_errors:
            raise ValidationException(
                message="게시글 유효성 검사에 실패했습니다.",
                field_errors=field_errors,
            )
        self.title = self.title.strip()
        self.content = self.content.strip()

    @classmethod
    def create(
        cls,
        board_info: BoardInfo,
        title: str,
        content: str,
        author: Author,
        hasher: PasswordHasher,
        raw_guest_password: str | None = None,
    ) -> "Post":
        """신규 게시글 생성 (비회원이면 비밀번호를 해시해 함께 보관)"""
        guest_password = None
        if author.is_guest:
            guest_password = GuestPassword.create(raw_guest_password or "", hasher)

        return cls(
            board_info=board_info,
            title=title,
            content=content,
            author=author,
            guest_password=guest_password,
        )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def can_modify_or_delete(
        self,
        requester_id: uuid.UUID | None,
        requester_role: Role | None,
        raw_guest_password: str | None,
        hasher: PasswordHasher,
    ) -> bool:
        """수정·삭제 가능 여부 (관리자 → 회원 본인 → 비회원 비밀번호 순으로 확인)"""
        if requester_role == Role.ADMIN:
            return True
        if not self.author.is_guest:
            return self.author.is_owner(requester_id)
        return self.guest_password is not None and self.guest_password.verify(raw_guest_password, hasher)

    def update_content(self, title: str, content: str) -> None:
        """제목·본문 수정"""
        if self.is_deleted:
            raise BadRequestException(
                message="삭제된 게시글은 수정할 수 없습니다.",
                error_code="POST_ALREADY_DELETED",
            )
        field_errors = self._collect_content_errors(title, content)
        if field_errors:
            raise ValidationException(
                message="게시글 수정 유효성 검사에 실패했습니다.",
                field_errors=field_errors,
            )
        self.title = title.strip()
        self.content = content.strip()
        self.modified_at = datetime.now(timezone.utc)

    def delete(self) -> None:
        """게시글 소프트 삭제"""
        if self.is_deleted:
            raise BadRequestException(
                message="이미 삭제된 게시글입니다.",
                error_code="POST_ALREADY_DELETED",
            )
        self.deleted_at = datetime.now(timezone.utc)

    @staticmethod
    def _collect_content_errors(title: str, content: str) -> dict[str, list[str]]:
        """제목·본문 규칙 위반 목록"""
        errors: dict[str, list[str]] = {}
        if not title or not title.strip():
            errors.setdefault("title", []).append("제목은 공백일 수 없습니다.")
        elif len(title.strip()) > TITLE_MAX:
            errors.setdefault("title", []).append(f"제목은 {TITLE_MAX}자 이하여야 합니다.")
        if not content or not content.strip():
            errors.setdefault("content", []).append("본문은 공백일 수 없습니다.")
        elif len(content.strip()) > CONTENT_MAX:
            errors.setdefault("content", []).append(f"본문은 {CONTENT_MAX}자 이하여야 합니다.")
        return errors
