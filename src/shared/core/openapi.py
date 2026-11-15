"""
Swagger(OpenAPI) 에러 응답 문서화 도구

라우터 데코레이터의 responses=에 넣을 값을 만든다.
    @router.get("/...", responses=error_responses(AUTH_ERRORS, {404: ["POST_NOT_FOUND"]}, VALIDATION_ERRORS))
- 상태 코드마다 발생할 수 있는 에러 코드 목록을 설명에 적고, 첫 번째 코드로 응답 예시를 만든다.
- 422를 직접 문서화하면 FastAPI가 자동으로 붙이는 기본 422(HTTPValidationError, {"detail": [...]})를 대신한다.
    (실제 422 응답은 APIResponse 형식이라 기본 문서는 실제와 다르다.)
- 에러 코드와 메시지는 실제 코드에서 raise 하는 값과 같게 ERROR_MESSAGES에 모아 둔다.
- restore_error_example_nulls: FastAPI가 문서를 만들 때 null 값을 지우므로(exclude_none)
    에러 예시에 errors·data(null)를 다시 채워 실제 응답 6개 필드와 같게 보여준다.
"""

from typing import Any
from fastapi import FastAPI, status

from shared.core.schemas import ErrorResponse

# 에러 코드 → 응답 메시지 (예시 생성용, 실제 예외 메시지와 같게 유지)
ERROR_MESSAGES: dict[str, str] = {
    # 공통
    "REQUEST_VALIDATION_ERROR": "요청 입력값 검증에 실패했습니다.",
    "VALIDATION_ERROR": "유효성 검사에 실패했습니다.",
    # 인증 (토큰)
    "TOKEN_REQUIRED": "인증 토큰이 필요합니다.",
    "INVALID_TOKEN": "유효하지 않은 토큰입니다.",
    "TOKEN_EXPIRED": "만료된 토큰입니다. 다시 로그인해주세요.",
    "TOKEN_REVOKED": "로그아웃된 토큰입니다.",
    "USER_NOT_FOUND": "존재하지 않는 사용자입니다.",
    "INVALID_CREDENTIALS": "이메일 또는 비밀번호가 올바르지 않습니다.",
    # 회원
    "USER_ALREADY_WITHDRAWN": "탈퇴한 회원은 서비스를 이용할 수 없습니다.",
    "ADMIN_PERMISSION_DENIED": "관리자 권한이 필요합니다.",
    "EMAIL_ALREADY_EXISTS": "이미 사용 중인 이메일입니다.",
    "INVALID_OLD_PASSWORD": "기존 비밀번호가 일치하지 않습니다.",
    "SAME_PASSWORD": "새 비밀번호는 이전 비밀번호와 동일할 수 없습니다.",
    # 게시판
    "BOARD_NOT_FOUND": "존재하지 않거나 삭제된 게시판입니다.",
    "BOARD_ID_ALREADY_EXISTS": "이미 사용 중인 게시판 ID입니다 ('freetalk').",
    # 게시글
    "POST_NOT_FOUND": "존재하지 않거나 삭제된 게시글입니다.",
    "POST_WRITE_DENIED": "이 게시판에 글을 작성할 권한이 없습니다.",
    "POST_LIST_DENIED": "이 게시판의 글 목록을 볼 권한이 없습니다.",
    "POST_VIEW_DENIED": "이 게시판의 글을 볼 권한이 없습니다.",
    "POST_EDIT_DENIED": "이 게시판의 글을 수정·삭제할 권한이 없습니다.",
    "NOT_POST_OWNER": "작성자 본인만 수정·삭제할 수 있습니다. 비회원 글은 작성 시 등록한 비밀번호가 필요합니다.",
}

# 422 예시에 넣을 필드별 오류 (errors 필드 모양을 보여주기 위한 값)
VALIDATION_EXAMPLE_ERRORS = {"field_name": ["오류 내용"]}

STATUS_TITLES: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "잘못된 요청",
    status.HTTP_401_UNAUTHORIZED: "인증 실패",
    status.HTTP_403_FORBIDDEN: "권한 없음",
    status.HTTP_404_NOT_FOUND: "리소스 없음",
    status.HTTP_409_CONFLICT: "중복 충돌",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "입력값 검증 실패",
}

# 자주 쓰는 에러 묶음
# 로그인 필수 API: 토큰 없음·위조·만료·로그아웃·회원 없음
AUTH_ERRORS: dict[int, list[str]] = {
    401: ["TOKEN_REQUIRED", "INVALID_TOKEN", "TOKEN_EXPIRED", "TOKEN_REVOKED", "USER_NOT_FOUND"],
    403: ["USER_ALREADY_WITHDRAWN"],
}
# 로그인 선택 API: 토큰 없이도 되지만, 보낸 토큰이 잘못됐으면 401
OPTIONAL_AUTH_ERRORS: dict[int, list[str]] = {
    401: ["INVALID_TOKEN", "TOKEN_EXPIRED", "TOKEN_REVOKED", "USER_NOT_FOUND"],
    403: ["USER_ALREADY_WITHDRAWN"],
}
# 관리자 전용 API
ADMIN_ERRORS: dict[int, list[str]] = {
    401: AUTH_ERRORS[401],
    403: ["ADMIN_PERMISSION_DENIED", "USER_ALREADY_WITHDRAWN"],
}
# 요청 바디가 있는 API: 스키마 검증 실패(형식·길이·타입) + 도메인 규칙 위반
VALIDATION_ERRORS: dict[int, list[str]] = {
    422: ["REQUEST_VALIDATION_ERROR", "VALIDATION_ERROR"],
}
# 경로·쿼리 값만 받는 API: 스키마 검증 실패만 (예: post_id에 숫자가 아닌 값)
REQUEST_ERRORS: dict[int, list[str]] = {
    422: ["REQUEST_VALIDATION_ERROR"],
}


def error_responses(*groups: dict[int, list[str]]) -> dict[int | str, dict[str, Any]]:
    """에러 묶음들을 합쳐 FastAPI responses= 값 생성 (같은 상태 코드는 에러 코드를 이어 붙임)"""
    merged: dict[int, list[str]] = {}
    for group in groups:
        for status_code, codes in group.items():
            bucket = merged.setdefault(status_code, [])
            bucket.extend(code for code in codes if code not in bucket)

    responses: dict[int | str, dict[str, Any]] = {}
    for status_code in sorted(merged):
        codes = merged[status_code]
        first = codes[0]
        example = {
            "success": False,
            "code": first,
            "message": ERROR_MESSAGES.get(first, ""),
            "errors": VALIDATION_EXAMPLE_ERRORS if status_code == 422 else None,
            "data": None,
            "responded_at": "2026-11-16T00:00:00Z",
        }
        responses[status_code] = {
            "model": ErrorResponse,
            "description": f"{STATUS_TITLES.get(status_code, '에러')} — code: " + ", ".join(f"`{c}`" for c in codes),
            "content": {"application/json": {"example": example}},
        }
    return responses


# 실제 에러 응답과 같은 필드 순서
ERROR_FIELD_ORDER = ("success", "code", "message", "errors", "data", "responded_at")


def restore_error_example_nulls(app: FastAPI) -> None:
    """Swagger 에러 예시에 null 필드(errors·data)를 다시 채우도록 app.openapi 교체"""
    default_openapi = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:  # 처음 한 번만 만들고 이후에는 저장된 문서를 쓴다.
            return app.openapi_schema
        schema = default_openapi()
        for operations in schema.get("paths", {}).values():
            for operation in operations.values():
                for response in operation.get("responses", {}).values():
                    content = response.get("content", {}).get("application/json", {})
                    example = content.get("example")
                    if isinstance(example, dict) and example.get("success") is False:
                        content["example"] = {key: example.get(key) for key in ERROR_FIELD_ORDER}
        return schema

    app.openapi = custom_openapi
