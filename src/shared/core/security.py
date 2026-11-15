"""
공통 인증 스키마 (Bearer 토큰)

Authorization: Bearer {토큰} 헤더를 읽는 FastAPI 보안 스키마.
여러 도메인(user, auth, board)의 의존성 선언에 같이 쓰기 위해 공통 모듈에 둔다.
- Swagger 상단에 Authorize 버튼이 생기고, 이 스키마를 선언한 API에는 자물쇠 아이콘이 붙는다.
- 자물쇠가 붙은 API만 Swagger "Try it out"에서 토큰을 헤더에 실어 보낸다.
- auto_error=False: 토큰이 없어도 FastAPI가 바로 에러를 내지 않고 None을 넘긴다.
    (401 응답은 우리가 UnauthorizedException으로 직접 내서 공통 응답 형식을 유지한다.)
"""

from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="로그인 API로 발급받은 access_token 값을 입력하세요. (Bearer 접두어 없이)",
)
