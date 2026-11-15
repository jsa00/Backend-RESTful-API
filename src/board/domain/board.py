"""
게시판 설정 엔티티 (도메인 계층)

게시판 하나 = 게시판 설정 하나. 관리자가 게시판을 만들고 이용 권한·목록 노출 개수를 정한다.

게시판 규칙
1. 게시판은 개수 제한 없이 만들 수 있다.
2. 게시판 ID는 영문 소문자로 시작하고 영문 소문자·숫자·하이픈·언더스코어만 쓸 수 있다. (2~30자)
    대문자로 입력해도 소문자로 바꿔 저장한다.
3. 비회원·회원·관리자 역할별로 아래 5가지 이용 권한을 설정할 수 있다.
    - edit_role: 게시글 작성·수정·삭제
    - view_role: 게시글 상세 보기
    - list_role: 게시글 목록 보기
    - comment_list_role: 댓글 목록 보기
    - comment_edit_role: 댓글 작성·수정·삭제
4. 게시글 목록 노출 개수(page_size)는 1~100이며 기본값은 20이다.
5. 게시판은 소프트 삭제하며, 삭제된 게시판은 수정할 수 없다.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from board.domain.enums import Role
from shared.core.exceptions import BadRequestException, ValidationException

# 게시판 ID 형식: 소문자로 시작 + 소문자·숫자·-·_ 1~29자 (총 2~30자)
BOARD_ID_REGEX = re.compile(r"^[a-z][a-z0-9_-]{1,29}$")

PAGE_SIZE_MIN = 1
PAGE_SIZE_MAX = 100
BOARD_NAME_MAX = 50


@dataclass(frozen=True)
class Authority:
    """게시판 세부 권한 값 객체 (frozen=True라 바꿀 때는 새 객체로 교체)"""

    edit_role: Role = Role.ALL
    view_role: Role = Role.ALL
    list_role: Role = Role.ALL
    comment_list_role: Role = Role.ALL
    comment_edit_role: Role = Role.ALL

    def can_edit(self, user_role: Role | str | None) -> bool:
        return self._check(user_role, self.edit_role)

    def can_view(self, user_role: Role | str | None) -> bool:
        return self._check(user_role, self.view_role)

    def can_list(self, user_role: Role | str | None) -> bool:
        return self._check(user_role, self.list_role)

    def can_view_comments(self, user_role: Role | str | None) -> bool:
        return self._check(user_role, self.comment_list_role)

    def can_edit_comments(self, user_role: Role | str | None) -> bool:
        return self._check(user_role, self.comment_edit_role)

    @staticmethod
    def _check(user_role: Role | str | None, required: Role) -> bool:
        # 비회원(None)은 ALL로 열린 기능만 이용할 수 있다.
        if user_role is None:
            return required == Role.ALL
        if isinstance(user_role, str):
            user_role = Role(user_role)
        return user_role.satisfies(required)


@dataclass
class Board:
    """게시판 설정 엔티티"""

    board_id: str  # 게시판 ID (예: freetalk, qna)
    board_name: str  # 게시판 이름 (예: 자유게시판)
    authority: Authority = field(default_factory=Authority)
    page_size: int = 20

    created_at: datetime | None = None
    modified_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self):
        # 여러 필드 오류를 한 번에 모아 422로 돌려준다.
        field_errors: dict[str, list[str]] = {}

        # 1) board_id: 앞뒤 공백 제거 + 소문자로 정규화한 뒤 형식 검사
        normalized_id = normalize_board_id(self.board_id)
        if not normalized_id:
            field_errors.setdefault("board_id", []).append("게시판 ID는 필수 입력값입니다.")
        elif not BOARD_ID_REGEX.match(normalized_id):
            field_errors.setdefault("board_id", []).append(
                "게시판 ID는 영문 소문자로 시작하고, 영문 소문자·숫자·-·_ 로 2~30자여야 합니다."
            )
        else:
            self.board_id = normalized_id

        # 2) board_name, page_size
        field_errors.update(self._collect_config_errors(self.board_name, self.page_size))

        if field_errors:
            raise ValidationException(
                message="게시판 설정 유효성 검사에 실패했습니다.",
                field_errors=field_errors,
            )
        self.board_name = self.board_name.strip()

    @classmethod
    def create(
        cls,
        board_id: str,
        board_name: str,
        authority: Authority | None = None,
        page_size: int = 20,
    ) -> "Board":
        """신규 게시판 생성"""
        return cls(
            board_id=board_id,
            board_name=board_name,
            authority=authority or Authority(),
            page_size=page_size,
        )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def update_config(
        self,
        board_name: str,
        page_size: int,
        authority: Authority | None = None,
    ) -> None:
        """게시판 설정 수정 (authority가 None이면 기존 권한 유지)"""
        if self.is_deleted:
            raise BadRequestException(
                message="삭제된 게시판 설정은 수정할 수 없습니다.",
                error_code="BOARD_ALREADY_DELETED",
            )

        field_errors = self._collect_config_errors(board_name, page_size)
        if field_errors:
            raise ValidationException(
                message="게시판 설정 수정 유효성 검사에 실패했습니다.",
                field_errors=field_errors,
            )

        self.board_name = board_name.strip()
        self.page_size = page_size
        if authority is not None:
            self.authority = authority
        self.modified_at = datetime.now(timezone.utc)

    def delete(self) -> None:
        """게시판 소프트 삭제"""
        if self.is_deleted:
            raise BadRequestException(
                message="이미 삭제된 게시판입니다.",
                error_code="BOARD_ALREADY_DELETED",
            )
        self.deleted_at = datetime.now(timezone.utc)

    @staticmethod
    def _collect_config_errors(board_name: str, page_size: int) -> dict[str, list[str]]:
        """게시판 이름·노출 개수 규칙 위반 목록"""
        errors: dict[str, list[str]] = {}
        if not board_name or not board_name.strip():
            errors.setdefault("board_name", []).append("게시판 이름은 공백일 수 없습니다.")
        elif len(board_name.strip()) > BOARD_NAME_MAX:
            errors.setdefault("board_name", []).append(f"게시판 이름은 {BOARD_NAME_MAX}자 이하여야 합니다.")
        if not (PAGE_SIZE_MIN <= page_size <= PAGE_SIZE_MAX):
            errors.setdefault("page_size", []).append(
                f"게시글 목록 노출 개수는 {PAGE_SIZE_MIN}~{PAGE_SIZE_MAX} 사이여야 합니다."
            )
        return errors


def normalize_board_id(board_id: str | None) -> str:
    """게시판 ID 정규화 (앞뒤 공백 제거 + 소문자)"""
    return (board_id or "").strip().lower()
