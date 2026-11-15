"""
게시판 응용 서비스 (응용 계층)

BoardService: 게시판 설정 생성·조회·목록·수정·삭제 유스케이스
권한(관리자 여부) 확인은 라우터의 require_admin_role 의존성이 먼저 끝낸 상태로 들어온다.
"""

from board.domain.board import Authority, Board, normalize_board_id
from board.domain.repository.board_repository import BoardRepository
from shared.core.exceptions import ConflictException, NotFoundException


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
