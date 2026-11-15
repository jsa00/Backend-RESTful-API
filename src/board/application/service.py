"""
게시판 응용 서비스 (응용 계층)

BoardService: 게시판 설정 생성·조회·목록·수정·삭제 유스케이스
    권한(관리자 여부) 확인은 라우터의 require_admin_role 의존성이 먼저 끝낸 상태로 들어온다.
PostService: 게시글 작성·목록·상세·수정·삭제 유스케이스
    게시판 권한(edit/view/list_role) 확인 → 작성자·비밀번호 확인 → 엔티티 규칙 순서로 처리한다.
"""

import uuid
from dataclasses import dataclass

from board.domain.board import Authority, Board, normalize_board_id
from board.domain.enums import PostSearchType, Role
from board.domain.post import Author, BoardInfo, Post
from board.domain.repository.board_repository import BoardRepository
from board.domain.repository.post_repository import PostRepository
from board.domain.service import PasswordHasher
from shared.core.exceptions import ConflictException, ForbiddenException, NotFoundException


class BoardService:
    """게시판 설정 서비스"""

    def __init__(self, board_repo: BoardRepository):
        self._board_repo = board_repo

    async def create_board(
        self,
        board_id: str,
        board_name: str,
        authority: Authority | None = None,
        page_size: int = 20,
    ) -> Board:
        """게시판 생성"""
        # 1) 엔티티를 먼저 만들어 ID를 소문자로 정규화하고 규칙을 검사한다.
        #    (정규화 전 값으로 중복 확인하면 "FreeTalk"이 기존 "freetalk"을 덮어쓸 수 있다.)
        board = Board.create(
            board_id=board_id,
            board_name=board_name,
            authority=authority,
            page_size=page_size,
        )

        # 2) 정규화된 ID로 중복 확인 (삭제된 게시판 ID도 다시 쓸 수 없음)
        if await self._board_repo.exists_by_id(board.board_id):
            raise ConflictException(
                message=f"이미 사용 중인 게시판 ID입니다 ('{board.board_id}').",
                error_code="BOARD_ID_ALREADY_EXISTS",
            )
        return await self._board_repo.save(board)

    async def get_board(self, board_id: str) -> Board:
        """게시판 단건 조회 (없거나 삭제됐으면 404)"""
        board = await self._board_repo.find_by_id(normalize_board_id(board_id))
        if not board:
            raise NotFoundException(
                message="존재하지 않거나 삭제된 게시판입니다.",
                error_code="BOARD_NOT_FOUND",
            )
        return board

    async def get_all_boards(self, include_deleted: bool = False) -> list[Board]:
        """게시판 목록 조회"""
        return await self._board_repo.find_all(include_deleted=include_deleted)

    async def update_board_config(
        self,
        board_id: str,
        board_name: str,
        page_size: int,
        authority: Authority | None = None,
    ) -> Board:
        """게시판 설정 수정"""
        board = await self.get_board(board_id)
        board.update_config(board_name=board_name, page_size=page_size, authority=authority)
        return await self._board_repo.save(board)

    async def delete_board(self, board_id: str) -> None:
        """게시판 소프트 삭제"""
        board = await self.get_board(board_id)
        board.delete()
        await self._board_repo.save(board)


@dataclass(frozen=True)
class PostPage:
    """게시글 목록 한 페이지 결과"""

    items: list[Post]
    total_count: int  # 검색 조건에 맞는 전체 글 수
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        # 올림 나눗셈 (글이 없으면 0페이지)
        return (self.total_count + self.page_size - 1) // self.page_size


class PostService:
    """게시글 서비스"""

    def __init__(
        self,
        post_repo: PostRepository,
        board_repo: BoardRepository,
        password_hasher: PasswordHasher,
    ):
        self._post_repo = post_repo
        self._board_repo = board_repo
        self._hasher = password_hasher

    async def write_post(
        self,
        board_id: str,
        title: str,
        content: str,
        author: Author,
        user_role: Role | None,
        raw_guest_password: str | None = None,
    ) -> Post:
        """게시글 작성 (author가 비회원이면 비밀번호 필수)"""
        board = await self._get_active_board(board_id)
        if not board.authority.can_edit(user_role):
            raise ForbiddenException(
                message="이 게시판에 글을 작성할 권한이 없습니다.",
                error_code="POST_WRITE_DENIED",
            )

        post = Post.create(
            board_info=BoardInfo(board_id=board.board_id, board_name=board.board_name),
            title=title,
            content=content,
            author=author,
            hasher=self._hasher,
            raw_guest_password=raw_guest_password,
        )
        return await self._post_repo.save(post)

    async def list_posts(
        self,
        board_id: str,
        user_role: Role | None,
        page: int = 1,
        page_size: int | None = None,
        search_type: PostSearchType = PostSearchType.ALL,
        keyword: str | None = None,
    ) -> PostPage:
        """게시글 목록 (최신순, page_size를 생략하면 게시판 설정값 사용)"""
        board = await self._get_active_board(board_id)
        if not board.authority.can_list(user_role):
            raise ForbiddenException(
                message="이 게시판의 글 목록을 볼 권한이 없습니다.",
                error_code="POST_LIST_DENIED",
            )

        size = page_size or board.page_size
        keyword = keyword.strip() if keyword and keyword.strip() else None
        items = await self._post_repo.find_by_board_id(
            board_id=board.board_id,
            limit=size,
            offset=(page - 1) * size,
            search_type=search_type,
            keyword=keyword,
        )
        total = await self._post_repo.count_by_board_id(
            board_id=board.board_id,
            search_type=search_type,
            keyword=keyword,
        )
        return PostPage(items=items, total_count=total, page=page, page_size=size)

    async def get_post_detail(self, post_id: int, user_role: Role | None) -> Post:
        """게시글 상세 (조회수 1 증가)"""
        post = await self._get_active_post(post_id)
        board = await self._get_active_board(post.board_info.board_id)
        if not board.authority.can_view(user_role):
            raise ForbiddenException(
                message="이 게시판의 글을 볼 권한이 없습니다.",
                error_code="POST_VIEW_DENIED",
            )

        await self._post_repo.increase_view_count(post_id)
        post.view_count += 1  # 응답에도 증가한 값을 보여준다.
        return post

    async def update_post(
        self,
        post_id: int,
        title: str,
        content: str,
        requester_id: uuid.UUID | None,
        user_role: Role | None,
        guest_password: str | None = None,
    ) -> Post:
        """게시글 수정"""
        post = await self._get_editable_post(post_id, requester_id, user_role, guest_password)
        post.update_content(title=title, content=content)
        return await self._post_repo.save(post)

    async def delete_post(
        self,
        post_id: int,
        requester_id: uuid.UUID | None,
        user_role: Role | None,
        guest_password: str | None = None,
    ) -> None:
        """게시글 소프트 삭제"""
        post = await self._get_editable_post(post_id, requester_id, user_role, guest_password)
        post.delete()
        await self._post_repo.save(post)

    async def _get_editable_post(
        self,
        post_id: int,
        requester_id: uuid.UUID | None,
        user_role: Role | None,
        guest_password: str | None,
    ) -> Post:
        """수정·삭제 가능한 게시글 조회 (게시판 edit 권한 + 작성자·비밀번호 확인)"""
        post = await self._get_active_post(post_id)
        board = await self._get_active_board(post.board_info.board_id)

        # 1) 게시판의 글쓰기 권한 (권한이 바뀌어 지금은 쓸 수 없는 게시판이면 수정·삭제도 불가)
        if not board.authority.can_edit(user_role):
            raise ForbiddenException(
                message="이 게시판의 글을 수정·삭제할 권한이 없습니다.",
                error_code="POST_EDIT_DENIED",
            )
        # 2) 작성자 본인·관리자·비회원 비밀번호 확인
        if not post.can_modify_or_delete(requester_id, user_role, guest_password, self._hasher):
            raise ForbiddenException(
                message="작성자 본인만 수정·삭제할 수 있습니다. 비회원 글은 작성 시 등록한 비밀번호가 필요합니다.",
                error_code="NOT_POST_OWNER",
            )
        return post

    async def _get_active_post(self, post_id: int) -> Post:
        post = await self._post_repo.find_by_id(post_id)
        if post is None:
            raise NotFoundException(
                message="존재하지 않거나 삭제된 게시글입니다.",
                error_code="POST_NOT_FOUND",
            )
        return post

    async def _get_active_board(self, board_id: str) -> Board:
        board = await self._board_repo.find_by_id(normalize_board_id(board_id))
        if board is None:
            raise NotFoundException(
                message="존재하지 않거나 삭제된 게시판입니다.",
                error_code="BOARD_NOT_FOUND",
            )
        return board
