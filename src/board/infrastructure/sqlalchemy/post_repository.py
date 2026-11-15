"""
게시글 저장소 구현체 (인프라 계층)

도메인의 PostRepository 인터페이스를 SQLAlchemy로 구현한다.
- 목록·개수는 같은 검색 조건(_search_filter)을 써서 페이지 수가 어긋나지 않게 한다.
- 검색은 대소문자를 구분하지 않는 부분 일치(ILIKE)다.
- 조회수는 UPDATE ... SET view_count = view_count + 1 로 DB에서 원자적으로 올린다.
"""

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from board.domain.enums import PostSearchType
from board.domain.post import Post
from board.domain.repository.post_repository import PostRepository
from board.infrastructure.sqlalchemy.mappers import PostMapper
from board.infrastructure.sqlalchemy.models import PostModel


class SqlAlchemyPostRepository(PostRepository):
    """SQLAlchemy 기반 PostRepository 구현체"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _search_filter(search_type: PostSearchType, keyword: str | None):
        """검색 대상별 WHERE 조건 (키워드가 없으면 None)"""
        if not keyword:
            return None
        title = PostModel.title.icontains(keyword, autoescape=True)
        content = PostModel.content.icontains(keyword, autoescape=True)
        author = PostModel.author_name.icontains(keyword, autoescape=True)
        match search_type:
            case PostSearchType.TITLE:
                return title
            case PostSearchType.CONTENT:
                return content
            case PostSearchType.TITLE_CONTENT:
                return or_(title, content)
            case PostSearchType.AUTHOR_NAME:
                return author
            case _:
                return or_(title, content, author)

    def _board_posts(self, stmt, board_id: str, search_type: PostSearchType, keyword: str | None):
        """게시판의 삭제되지 않은 글 + 검색 조건 적용"""
        stmt = stmt.where(PostModel.board_id == board_id, PostModel.deleted_at.is_(None))
        condition = self._search_filter(search_type, keyword)
        return stmt if condition is None else stmt.where(condition)

    async def find_by_id(self, post_id: int) -> Post | None:
        stmt = select(PostModel).where(
            PostModel.post_id == post_id,
            PostModel.deleted_at.is_(None),
        )
        model = await self.session.scalar(stmt)
        return PostMapper.to_domain(model) if model else None

    async def find_by_board_id(
        self,
        board_id: str,
        limit: int,
        offset: int,
        search_type: PostSearchType = PostSearchType.ALL,
        keyword: str | None = None,
    ) -> list[Post]:
        stmt = self._board_posts(select(PostModel), board_id, search_type, keyword)
        stmt = stmt.order_by(PostModel.post_id.desc()).offset(offset).limit(limit)
        models = (await self.session.scalars(stmt)).all()
        return [PostMapper.to_domain(model) for model in models]

    async def count_by_board_id(
        self,
        board_id: str,
        search_type: PostSearchType = PostSearchType.ALL,
        keyword: str | None = None,
    ) -> int:
        stmt = self._board_posts(select(func.count(PostModel.post_id)), board_id, search_type, keyword)
        return await self.session.scalar(stmt) or 0

    async def increase_view_count(self, post_id: int) -> None:
        # modified_at을 자기 자신으로 지정해 onupdate(수정 시각 자동 기록)가 동작하지 않게 한다.
        # (조회는 글 수정이 아니므로 수정 일시가 바뀌면 안 된다.)
        stmt = (
            update(PostModel)
            .where(PostModel.post_id == post_id)
            .values(view_count=PostModel.view_count + 1, modified_at=PostModel.modified_at)
        )
        await self.session.execute(stmt)

    async def save(self, post: Post) -> Post:
        if post.post_id is None:
            # 신규 게시글 등록(INSERT)
            model = PostMapper.to_model(post)
            self.session.add(model)
        else:
            # 기존 게시글 수정(UPDATE) - 제목·본문·삭제 시각 (modified_at은 onupdate가 기록)
            model = await self.session.get(PostModel, post.post_id)
            model.title = post.title
            model.content = post.content
            model.deleted_at = post.deleted_at

        await self.session.flush()
        await self.session.refresh(model)
        return PostMapper.to_domain(model)
