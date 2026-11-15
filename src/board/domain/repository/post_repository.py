"""
게시글 저장소 인터페이스 (도메인 계층)

구현: infrastructure/sqlalchemy/post_repository.py
"""

from abc import ABC, abstractmethod
from board.domain.enums import PostSearchType
from board.domain.post import Post


class PostRepository(ABC):
    """게시글 저장소 인터페이스"""

    @abstractmethod
    async def find_by_id(self, post_id: int) -> Post | None:
        """게시글 번호 기준 단건 조회 (삭제된 글 제외)"""

    @abstractmethod
    async def find_by_board_id(
        self,
        board_id: str,
        limit: int,
        offset: int,
        search_type: PostSearchType = PostSearchType.ALL,
        keyword: str | None = None,
    ) -> list[Post]:
        """게시판의 게시글 목록 (최신순, 페이징·검색)"""

    @abstractmethod
    async def count_by_board_id(
        self,
        board_id: str,
        search_type: PostSearchType = PostSearchType.ALL,
        keyword: str | None = None,
    ) -> int:
        """게시판의 게시글 수 (목록과 같은 검색 조건, 전체 페이지 수 계산용)"""

    @abstractmethod
    async def increase_view_count(self, post_id: int) -> None:
        """조회수 1 증가 (동시에 여러 요청이 와도 빠지지 않도록 DB에서 원자적으로)"""

    @abstractmethod
    async def save(self, post: Post) -> Post:
        """신규 생성(INSERT) 또는 변경 사항 반영(UPDATE)"""
