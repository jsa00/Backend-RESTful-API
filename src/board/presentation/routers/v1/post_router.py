"""
게시글 API 라우터 (표현 계층)

| 메서드 | 경로                            | 기능                    | 권한                                   |
| POST   | /v1/boards/{board_id}/posts     | 게시글 작성             | 게시판 edit_role                        |
| GET    | /v1/boards/{board_id}/posts     | 게시글 목록(페이징·검색) | 게시판 list_role                        |
| GET    | /v1/posts/{post_id}             | 게시글 상세(조회수 +1)  | 게시판 view_role                        |
| PUT    | /v1/posts/{post_id}             | 게시글 수정             | edit_role + 작성자 본인/관리자/비회원 비밀번호 |
| DELETE | /v1/posts/{post_id}             | 게시글 삭제(소프트)     | edit_role + 작성자 본인/관리자/비회원 비밀번호 |

로그인 회원은 토큰만 보내면 되고, 비회원은
- 작성: 바디에 guest_name·guest_password
- 수정: 바디에 guest_password
- 삭제: X-Guest-Password 헤더 (DELETE 요청 바디는 표준 동작이 아니라 헤더로 받는다.)
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Header, Path, Query, status

from board.application.service import PostService
from board.domain.enums import PostSearchType, Role
from board.domain.post import Author
from board.presentation.dependencies import (
    get_current_author,
    get_current_role,
    provide_post_service,
)
from board.presentation.schemas import (
    CreatePostRequest,
    PostDetailResponse,
    PostPageResponse,
    UpdatePostRequest,
)
from shared.core.exceptions import ValidationException
from shared.core.schemas import APIResponse

router = APIRouter(prefix="/v1", tags=["Posts"])

BoardIdPath = Annotated[str, Path(description="게시판 ID", examples=["freetalk"])]
PostIdPath = Annotated[int, Path(ge=1, description="게시글 번호", examples=[1])]
CurrentAuthor = Annotated[Author | None, Depends(get_current_author)]
CurrentRole = Annotated[Role | None, Depends(get_current_role)]
PostServiceDep = Annotated[PostService, Depends(provide_post_service)]


@router.post(
    "/boards/{board_id}/posts",
    response_model=APIResponse[PostDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="게시글 작성",
    description=(
        "게시판의 글쓰기 권한(edit_role)이 있어야 합니다. "
        "로그인 회원은 토큰으로 작성자가 정해지고, 비회원은 guest_name·guest_password가 필수입니다."
    ),
)
async def write_post(
    board_id: BoardIdPath,
    request: CreatePostRequest,
    current_author: CurrentAuthor,
    current_role: CurrentRole,
    post_service: PostServiceDep,
):
    if current_author is not None:
        # 로그인 회원: guest_* 필드는 무시한다.
        author, raw_password = current_author, None
    else:
        # 비회원: 닉네임·비밀번호가 모두 있어야 한다.
        missing = {
            field: ["비회원 글 작성 시 필수입니다."]
            for field in ("guest_name", "guest_password")
            if not getattr(request, field)
        }
        if missing:
            raise ValidationException(message="비회원 작성 정보가 없습니다.", field_errors=missing)
        author, raw_password = Author.guest(request.guest_name), request.guest_password

    post = await post_service.write_post(
        board_id=board_id,
        title=request.title,
        content=request.content,
        author=author,
        user_role=current_role,
        raw_guest_password=raw_password,
    )
    return APIResponse.ok(data=PostDetailResponse.from_domain(post), message="게시글이 등록되었습니다.")


@router.get(
    "/boards/{board_id}/posts",
    response_model=APIResponse[PostPageResponse],
    summary="게시글 목록 (페이징·검색)",
    description=(
        "게시판의 목록 보기 권한(list_role)이 있어야 합니다. 최신순으로 정렬하며, "
        "page_size를 생략하면 게시판 설정값을 사용합니다. 검색은 대소문자를 구분하지 않는 부분 일치입니다."
    ),
)
async def list_posts(
    board_id: BoardIdPath,
    current_role: CurrentRole,
    post_service: PostServiceDep,
    page: Annotated[int, Query(ge=1, le=10_000, description="페이지 번호 (1부터)")] = 1,
    page_size: Annotated[int | None, Query(ge=1, le=100, description="페이지당 게시글 수 (생략 시 게시판 설정값)")] = None,
    search_type: Annotated[PostSearchType, Query(description="검색 대상 (ALL은 제목+내용+작성자 이름)")] = PostSearchType.ALL,
    keyword: Annotated[str | None, Query(max_length=50, description="검색어")] = None,
):
    result = await post_service.list_posts(
        board_id=board_id,
        user_role=current_role,
        page=page,
        page_size=page_size,
        search_type=search_type,
        keyword=keyword,
    )
    return APIResponse.ok(data=PostPageResponse.from_page(result, search_type, keyword))


@router.get(
    "/posts/{post_id}",
    response_model=APIResponse[PostDetailResponse],
    summary="게시글 상세",
    description="게시판의 글 보기 권한(view_role)이 있어야 합니다. 조회할 때마다 조회수가 1 올라갑니다.",
)
async def get_post(
    post_id: PostIdPath,
    current_role: CurrentRole,
    post_service: PostServiceDep,
):
    post = await post_service.get_post_detail(post_id=post_id, user_role=current_role)
    return APIResponse.ok(data=PostDetailResponse.from_domain(post))


@router.put(
    "/posts/{post_id}",
    response_model=APIResponse[PostDetailResponse],
    summary="게시글 수정",
    description=(
        "게시판 글쓰기 권한이 있어야 하며, 회원 글은 작성자 본인·관리자만, "
        "비회원 글은 guest_password가 맞을 때(또는 관리자)만 수정할 수 있습니다."
    ),
)
async def update_post(
    post_id: PostIdPath,
    request: UpdatePostRequest,
    current_author: CurrentAuthor,
    current_role: CurrentRole,
    post_service: PostServiceDep,
):
    post = await post_service.update_post(
        post_id=post_id,
        title=request.title,
        content=request.content,
        requester_id=current_author.author_id if current_author else None,
        user_role=current_role,
        guest_password=request.guest_password,
    )
    return APIResponse.ok(data=PostDetailResponse.from_domain(post), message="게시글이 수정되었습니다.")


@router.delete(
    "/posts/{post_id}",
    response_model=APIResponse[None],
    summary="게시글 삭제",
    description=(
        "게시글을 소프트 삭제합니다. 권한 규칙은 수정과 같으며, "
        "비회원 글은 X-Guest-Password 헤더에 작성 시 등록한 비밀번호를 담아 보냅니다."
    ),
)
async def delete_post(
    post_id: PostIdPath,
    current_author: CurrentAuthor,
    current_role: CurrentRole,
    post_service: PostServiceDep,
    x_guest_password: Annotated[
        str | None, Header(max_length=72, description="비회원 글 비밀번호 (회원·관리자는 생략)")
    ] = None,
):
    await post_service.delete_post(
        post_id=post_id,
        requester_id=current_author.author_id if current_author else None,
        user_role=current_role,
        guest_password=x_guest_password,
    )
    return APIResponse.ok(message="게시글이 삭제되었습니다.")
