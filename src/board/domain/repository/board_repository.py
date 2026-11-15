"""
게시판 설정 저장소 인터페이스 (도메인 계층)

게시판을 어디에 어떻게 저장하는지는 모르고, 할 수 있는 일만 정의한다.
구현: infrastructure/sqlalchemy/board_repository.py
"""

from abc import ABC, abstractmethod
from board.domain.board import Board


class BoardRepository(ABC):
    """게시판 설정 저장소 인터페이스"""

    @abstractmethod
    async def find_by_id(self, board_id: str) -> Board | None:
        """게시판 ID 기준 단건 조회 (삭제된 게시판 제외)"""

    @abstractmethod
    async def find_all(self, include_deleted: bool = False) -> list[Board]:
        """게시판 목록 조회 (기본은 삭제된 게시판 제외)"""

    @abstractmethod
    async def exists_by_id(self, board_id: str) -> bool:
        """게시판 ID 사용 여부 (삭제된 게시판 포함, ID는 다시 쓸 수 없음)"""

    @abstractmethod
    async def save(self, board: Board) -> Board:
        """신규 생성(INSERT) 또는 변경 사항 반영(UPDATE)"""
