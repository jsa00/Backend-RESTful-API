"""
게시판 요청·응답 스키마 (표현 계층)

- AuthoritySchema: 게시판 권한 5가지 (값은 ALL / USER / ADMIN, 생략하면 ALL)
- CreateBoardRequest / UpdateBoardRequest: 게시판 생성·수정 요청 바디
- BoardResponse: 게시판 설정 응답 (APIResponse의 data에 담겨 나간다.)
- CreatePostRequest / UpdatePostRequest: 게시글 작성·수정 요청 바디 (비회원은 guest_* 필드 사용)
- PostListItemResponse / PostDetailResponse / PostPageResponse: 게시글 목록 항목·상세·페이지 응답
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from board.application.service import PostPage
from board.domain.board import Authority, Board
from board.domain.enums import PostSearchType, Role
from board.domain.post import Author, Post


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


# 게시글
class CreatePostRequest(BaseModel):
    """게시글 작성 요청 (로그인 회원은 guest_* 필드를 비워 두고, 비회원은 둘 다 필수)"""

    title: str = Field(min_length=1, max_length=200, description="제목 (1~200자)", examples=["첫 글입니다"])
    content: str = Field(min_length=1, max_length=10_000, description="본문 (1~10,000자)", examples=["안녕하세요. 반갑습니다."])
    guest_name: str | None = Field(
        default=None, min_length=1, max_length=20, description="비회원 닉네임 (비회원 필수, 1~20자)", examples=["손님"]
    )
    guest_password: str | None = Field(
        default=None, min_length=6, max_length=72, description="비회원 비밀번호 (비회원 필수, 6~72자, 수정·삭제 시 필요)", examples=["guest1234"]
    )


class UpdatePostRequest(BaseModel):
    """게시글 수정 요청"""

    title: str = Field(min_length=1, max_length=200, description="제목 (1~200자)", examples=["수정한 제목"])
    content: str = Field(min_length=1, max_length=10_000, description="본문 (1~10,000자)", examples=["수정한 본문입니다."])
    guest_password: str | None = Field(
        default=None, max_length=72, description="비회원 글이면 작성 시 등록한 비밀번호", examples=["guest1234"]
    )


class AuthorResponse(BaseModel):
    """작성자 정보 (회원 이메일 등 개인정보는 포함하지 않음)"""

    author_id: uuid.UUID | None = Field(None, description="회원 ID (비회원 글은 null)")
    author_name: str = Field(description="작성자 이름")
    is_guest: bool = Field(description="비회원 글 여부")

    @classmethod
    def from_domain(cls, author: Author) -> "AuthorResponse":
        return cls(author_id=author.author_id, author_name=author.author_name, is_guest=author.is_guest)


class PostListItemResponse(BaseModel):
    """게시글 목록 항목 (본문 제외)"""

    post_id: int = Field(description="게시글 번호")
    board_id: str = Field(description="게시판 ID")
    board_name: str = Field(description="게시판 이름")
    title: str = Field(description="제목")
    author: AuthorResponse = Field(description="작성자")
    view_count: int = Field(description="조회수")
    created_at: datetime | None = Field(None, description="작성 일시(UTC)")
    modified_at: datetime | None = Field(None, description="수정 일시(UTC)")

    @classmethod
    def from_domain(cls, post: Post) -> "PostListItemResponse":
        return cls(
            post_id=post.post_id,
            board_id=post.board_info.board_id,
            board_name=post.board_info.board_name,
            title=post.title,
            author=AuthorResponse.from_domain(post.author),
            view_count=post.view_count,
            created_at=post.created_at,
            modified_at=post.modified_at,
        )


class PostDetailResponse(PostListItemResponse):
    """게시글 상세 (본문 포함)"""

    content: str = Field(description="본문")

    @classmethod
    def from_domain(cls, post: Post) -> "PostDetailResponse":
        return cls(**PostListItemResponse.from_domain(post).model_dump(), content=post.content)


class PostPageResponse(BaseModel):
    """게시글 목록 페이지"""

    items: list[PostListItemResponse] = Field(description="게시글 목록 (최신순)")
    total_count: int = Field(description="검색 조건에 맞는 전체 게시글 수")
    page: int = Field(description="현재 페이지 (1부터)")
    page_size: int = Field(description="페이지당 게시글 수")
    total_pages: int = Field(description="전체 페이지 수")
    search_type: PostSearchType = Field(description="검색 대상")
    keyword: str | None = Field(None, description="검색어")

    @classmethod
    def from_page(cls, page: PostPage, search_type: PostSearchType, keyword: str | None) -> "PostPageResponse":
        return cls(
            items=[PostListItemResponse.from_domain(post) for post in page.items],
            total_count=page.total_count,
            page=page.page,
            page_size=page.page_size,
            total_pages=page.total_pages,
            search_type=search_type,
            keyword=keyword,
        )
