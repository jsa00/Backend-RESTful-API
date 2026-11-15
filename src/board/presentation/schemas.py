"""
게시판 요청·응답 스키마 (표현 계층)

- AuthoritySchema: 게시판 권한 5가지 (값은 ALL / USER / ADMIN, 생략하면 ALL)
- CreateBoardRequest / UpdateBoardRequest: 게시판 생성·수정 요청 바디
- BoardResponse: 게시판 설정 응답 (APIResponse의 data에 담겨 나간다.)
"""

from datetime import datetime
from pydantic import BaseModel, Field

from board.domain.board import Authority, Board
from board.domain.enums import Role


class AuthoritySchema(BaseModel):
    """게시판 권한 설정 (ALL: 비회원 포함 / USER: 회원 이상 / ADMIN: 관리자만)"""

    edit_role: Role = Field(default=Role.ALL, description="게시글 작성·수정·삭제 권한")
    view_role: Role = Field(default=Role.ALL, description="게시글 상세 보기 권한")
    list_role: Role = Field(default=Role.ALL, description="게시글 목록 보기 권한")
    comment_list_role: Role = Field(default=Role.ALL, description="댓글 목록 보기 권한")
    comment_edit_role: Role = Field(default=Role.ALL, description="댓글 작성·수정·삭제 권한")

    def to_domain(self) -> Authority:
        """요청 스키마 -> 도메인 값 객체"""
        return Authority(**self.model_dump())

    @classmethod
    def from_domain(cls, authority: Authority) -> "AuthoritySchema":
        return cls(
            edit_role=authority.edit_role,
            view_role=authority.view_role,
            list_role=authority.list_role,
            comment_list_role=authority.comment_list_role,
            comment_edit_role=authority.comment_edit_role,
        )


class CreateBoardRequest(BaseModel):
    """게시판 생성 요청"""

    board_id: str = Field(
        min_length=2,
        max_length=30,
        description="게시판 ID (영문 소문자로 시작, 영문 소문자·숫자·-·_ 2~30자, 대문자는 소문자로 저장)",
        examples=["freetalk"],
    )
    board_name: str = Field(
        min_length=1,
        max_length=50,
        description="게시판 이름",
        examples=["자유게시판"],
    )
    authority: AuthoritySchema = Field(
        default_factory=AuthoritySchema,
        description="권한 설정 (생략하면 모두 ALL)",
    )
    page_size: int = Field(default=20, ge=1, le=100, description="게시글 목록 노출 개수 (1~100)")


class UpdateBoardRequest(BaseModel):
    """게시판 설정 수정 요청 (게시판 ID는 바꿀 수 없음)"""

    board_name: str = Field(min_length=1, max_length=50, description="게시판 이름", examples=["자유게시판"])
    page_size: int = Field(default=20, ge=1, le=100, description="게시글 목록 노출 개수 (1~100)")
    authority: AuthoritySchema | None = Field(
        default=None,
        description="변경할 권한 설정 (생략하면 기존 권한 유지)",
    )


class BoardResponse(BaseModel):
    """게시판 설정 응답"""

    board_id: str = Field(description="게시판 ID")
    board_name: str = Field(description="게시판 이름")
    authority: AuthoritySchema = Field(description="권한 설정")
    page_size: int = Field(description="게시글 목록 노출 개수")
    created_at: datetime | None = Field(None, description="생성 일시(UTC)")
    modified_at: datetime | None = Field(None, description="수정 일시(UTC)")
    deleted_at: datetime | None = Field(None, description="삭제 일시(UTC, 삭제된 게시판 목록 조회 시에만 값 있음)")

    @classmethod
    def from_domain(cls, board: Board) -> "BoardResponse":
        return cls(
            board_id=board.board_id,
            board_name=board.board_name,
            authority=AuthoritySchema.from_domain(board.authority),
            page_size=board.page_size,
            created_at=board.created_at,
            modified_at=board.modified_at,
            deleted_at=board.deleted_at,
        )
