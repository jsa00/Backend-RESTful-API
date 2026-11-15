"""
관리자 지정 스크립트 (서버 관리용 CLI)

회원가입 API는 항상 USER 권한으로 가입하므로, 첫 관리자는 서버에서 이 스크립트로 지정한다.
관리자 지정 API를 따로 두지 않는 이유: 누구나 호출할 수 있는 경로가 생기지 않게 하기 위해서다.

사용법 (프로젝트 루트에서)
    1) 회원가입 API로 계정을 먼저 만든다.
    2) uv run python src/scripts/promote_admin.py 가입한이메일@example.com

.env의 DATABASE_URL로 접속하며, 앱과 같은 저장소(UserRepository)와 도메인 규칙(User.grant_admin)을 사용한다.
"""

import asyncio
import sys
from pathlib import Path

# src 폴더를 import 경로에 추가 (scripts 폴더에서 실행해도 shared·user 패키지를 찾을 수 있게)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.core.database import AsyncSessionLocal, close_db  # noqa: E402
from shared.core.exceptions import SharedException  # noqa: E402
from user.infrastructure.repositories import SqlAlchemyUserRepository  # noqa: E402


async def promote(email: str) -> int:
    """이메일로 회원을 찾아 관리자로 변경 후 종료 코드 반환 (0 성공, 1 실패)"""
    async with AsyncSessionLocal() as session:
        repo = SqlAlchemyUserRepository(session)
        user = await repo.find_by_email(email)
        if user is None:
            print(f"[실패] 가입되지 않은 이메일입니다: {email}")
            return 1
        try:
            user.grant_admin()
        except SharedException as err:
            print(f"[실패] {err.message}")
            return 1
        await repo.save(user)
        await session.commit()
        print(f"[완료] {user.email} ({user.name}) 회원을 관리자(ADMIN)로 지정했습니다.")
        return 0


async def main() -> int:
    if len(sys.argv) != 2:
        print("사용법: uv run python src/scripts/promote_admin.py <이메일>")
        return 1
    try:
        return await promote(sys.argv[1].strip())
    finally:
        await close_db()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
