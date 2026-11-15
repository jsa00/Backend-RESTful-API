"""
도메인 엔티티 <-> ORM 모델 변환기 (인프라 계층)

게시판 엔티티는 권한을 Authority 값 객체 하나로 묶어 갖지만,
테이블에는 권한 5개가 각각 컬럼으로 펼쳐져 있어서 변환 코드를 한곳에 모았다.
"""

from board.domain.board import Authority, Board
from board.domain.enums import Role
from board.infrastructure.sqlalchemy.models import BoardModel


class BoardMapper:
    """Board 엔티티 <-> BoardModel 변환"""

    @staticmethod
    def to_domain(model: BoardModel) -> Board:
        """ORM 모델 -> 도메인 엔티티 (권한 문자열 → Role)"""
        return Board(
            board_id=model.board_id,
            board_name=model.board_name,
            authority=Authority(
                edit_role=Role(model.edit_role),
                view_role=Role(model.view_role),
                list_role=Role(model.list_role),
                comment_list_role=Role(model.comment_list_role),
                comment_edit_role=Role(model.comment_edit_role),
            ),
            page_size=model.page_size,
            created_at=model.created_at,
            modified_at=model.modified_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(domain: Board) -> BoardModel:
        """도메인 엔티티 -> 신규 ORM 모델 (Role → 권한 문자열)"""
        return BoardModel(
            board_id=domain.board_id,
            board_name=domain.board_name,
            page_size=domain.page_size,
            **BoardMapper.role_columns(domain.authority),
        )

    @staticmethod
    def role_columns(authority: Authority) -> dict[str, str]:
        """Authority 값 객체 -> 권한 컬럼 5개 값"""
        return {
            "edit_role": authority.edit_role.value,
            "view_role": authority.view_role.value,
            "list_role": authority.list_role.value,
            "comment_list_role": authority.comment_list_role.value,
            "comment_edit_role": authority.comment_edit_role.value,
        }
