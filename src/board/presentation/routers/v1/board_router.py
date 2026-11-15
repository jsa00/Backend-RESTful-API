"""
게시판 설정 API 라우터 (표현 계층, /v1/boards)

| 메서드 | 경로                     | 기능                 | 권한                                |
| POST   | /v1/boards               | 게시판 생성          | 관리자                              |
| GET    | /v1/boards               | 게시판 목록          | 누구나 (include_deleted=true는 관리자) |
| GET    | /v1/boards/{board_id}    | 게시판 단건 조회     | 누구나                              |
| PUT    | /v1/boards/{board_id}    | 게시판 설정 수정     | 관리자                              |
| DELETE | /v1/boards/{board_id}    | 게시판 삭제(소프트)  | 관리자                              |
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status

from board.application.service import BoardService
from board.domain.enums import Role
from board.presentation.dependencies import (
    get_current_role,
    provide_board_service,
    require_admin_role,
)
from board.presentation.schemas import BoardResponse, CreateBoardRequest, UpdateBoardRequest
from shared.core.exceptions import ForbiddenException
from shared.core.schemas import APIResponse

router = APIRouter(prefix="/v1/boards", tags=["Boards"])

BoardIdPath = Annotated[str, Path(description="게시판 ID", examples=["freetalk"])]


@router.post(
    "",
    response_model=APIResponse[BoardResponse],
    status_code=status.HTTP_201_CREATED,
    summary="게시판 생성 (관리자)",
    description="게시판 ID·이름·권한·목록 노출 개수를 정해 새 게시판을 만듭니다.",
)
async def create_board(
    request: CreateBoardRequest,
    _: Annotated[Role, Depends(require_admin_role)],
    board_service: Annotated[BoardService, Depends(provide_board_service)],
):
    board = await board_service.create_board(
        board_id=request.board_id,
        board_name=request.board_name,
        authority=request.authority.to_domain(),
        page_size=request.page_size,
    )
    return APIResponse.ok(data=BoardResponse.from_domain(board), message="게시판이 생성되었습니다.")


@router.get(
    "",
    response_model=APIResponse[list[BoardResponse]],
    summary="게시판 목록",
    description="게시판 목록을 생성 순서대로 조회합니다. 삭제된 게시판까지 보려면 관리자 권한이 필요합니다.",
)
async def list_boards(
    current_role: Annotated[Role | None, Depends(get_current_role)],
    board_service: Annotated[BoardService, Depends(provide_board_service)],
    include_deleted: Annotated[bool, Query(description="삭제된 게시판 포함 여부 (관리자 전용)")] = False,
):
    # 삭제된 게시판은 관리자만 볼 수 있다.
    if include_deleted and current_role != Role.ADMIN:
        raise ForbiddenException(
            message="삭제된 게시판 목록은 관리자만 조회할 수 있습니다.",
            error_code="ADMIN_PERMISSION_DENIED",
        )
    boards = await board_service.get_all_boards(include_deleted=include_deleted)
    return APIResponse.ok(data=[BoardResponse.from_domain(board) for board in boards])


@router.get(
    "/{board_id}",
    response_model=APIResponse[BoardResponse],
    summary="게시판 단건 조회",
    description="게시판 설정(이름·권한·목록 노출 개수)을 조회합니다. 삭제된 게시판은 404입니다.",
)
async def get_board(
    board_id: BoardIdPath,
    board_service: Annotated[BoardService, Depends(provide_board_service)],
):
    board = await board_service.get_board(board_id)
    return APIResponse.ok(data=BoardResponse.from_domain(board))


@router.put(
    "/{board_id}",
    response_model=APIResponse[BoardResponse],
    summary="게시판 설정 수정 (관리자)",
    description="게시판 이름·목록 노출 개수·권한을 수정합니다. authority를 생략하면 기존 권한을 유지합니다.",
)
async def update_board(
    board_id: BoardIdPath,
    request: UpdateBoardRequest,
    _: Annotated[Role, Depends(require_admin_role)],
    board_service: Annotated[BoardService, Depends(provide_board_service)],
):
    board = await board_service.update_board_config(
        board_id=board_id,
        board_name=request.board_name,
        page_size=request.page_size,
        authority=request.authority.to_domain() if request.authority else None,
    )
    return APIResponse.ok(data=BoardResponse.from_domain(board), message="게시판 설정이 수정되었습니다.")


@router.delete(
    "/{board_id}",
    response_model=APIResponse[None],
    summary="게시판 삭제 (관리자)",
    description="게시판을 소프트 삭제합니다. 삭제된 게시판의 ID는 다시 사용할 수 없습니다.",
)
async def delete_board(
    board_id: BoardIdPath,
    _: Annotated[Role, Depends(require_admin_role)],
    board_service: Annotated[BoardService, Depends(provide_board_service)],
):
    await board_service.delete_board(board_id)
    return APIResponse.ok(message="게시판이 삭제되었습니다.")
