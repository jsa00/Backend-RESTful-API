"""
비회원 비밀번호 해싱 구현체 (인프라 계층)

board 도메인의 PasswordHasher 인터페이스를 bcrypt로 구현한다. (user 도메인의 구현과 방식은 같다.)
"""

import bcrypt
from board.domain.service import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """bcrypt 기반 PasswordHasher 구현체"""

    def hash(self, raw_password: str) -> str:
        return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))
