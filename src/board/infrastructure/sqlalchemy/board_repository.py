"""
게시판 설정 저장소 구현체 (인프라 계층)

도메인의 BoardRepository 인터페이스를 SQLAlchemy로 구현한다.
- 조회는 deleted_at이 비어 있는(삭제되지 않은) 게시판만 대상으로 한다.
- ID 중복 확인은 삭제된 게시판까지 포함한다. (게시판 ID가 기본키라 다시 쓸 수 없다.)
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from board.domain.board import Board
from board.domain.repository.board_repository import BoardRepository
from board.infrastructure.sqlalchemy.mappers import BoardMapper
from board.infrastructure.sqlalchemy.models import BoardModel


class SqlAlchemyBoardRepository(BoardRepository):
    """SQLAlchemy 기반 BoardRepository 구현체"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_id(self, board_id: str) -> Board | None:
        stmt = select(BoardModel).where(
            BoardModel.board_id == board_id,
            BoardModel.deleted_at.is_(None),
        )
        model = await self.session.scalar(stmt)
        return BoardMapper.to_domain(model) if model else None

    async def find_all(self, include_deleted: bool = False) -> list[Board]:
        # 생성 순서대로 정렬
        stmt = select(BoardModel).order_by(BoardModel.created_at)
        if not include_deleted:
            stmt = stmt.where(BoardModel.deleted_at.is_(None))
        models = (await self.session.scalars(stmt)).all()
        return [BoardMapper.to_domain(model) for model in models]

    async def exists_by_id(self, board_id: str) -> bool:
        # session.get: 기본키로 조회 (삭제 여부와 관계없이 찾는다.)
        return await self.session.get(BoardModel, board_id) is not None

    async def save(self, board: Board) -> Board:
        model = await self.session.get(BoardModel, board.board_id)
        if model is None:
            # 신규 게시판 등록(INSERT)
            model = BoardMapper.to_model(board)
            self.session.add(model)
        else:
            # 기존 게시판 수정(UPDATE) - 이름·노출 개수·권한·삭제 시각
            model.board_name = board.board_name
            model.page_size = board.page_size
            for column, value in BoardMapper.role_columns(board.authority).items():
                setattr(model, column, value)
            model.deleted_at = board.deleted_at

        await self.session.flush()
        await self.session.refresh(model)
        return BoardMapper.to_domain(model)
