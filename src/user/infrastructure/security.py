"""
비밀번호 해싱 구현체 (인프라 계층)

도메인의 PasswordHasher 인터페이스를 bcrypt 라이브러리로 실제 구현한다.
- hash: 매번 새 salt(무작위 값)를 섞어 해시하므로 같은 비밀번호도 해시값이 매번 다르다.
- verify: 저장된 해시에 들어 있는 salt를 꺼내 다시 해시한 뒤 비교한다.
- 결과 형식: "$2b$12$..." (60자, 12는 반복 강도 cost)
"""

import bcrypt
from user.domain.service import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """bcrypt 기반 PasswordHasher 구현체"""

    def hash(self, raw_password: str) -> str:
        # bcrypt는 bytes만 다루므로 문자열을 UTF-8 bytes로 바꿔서 넘긴다.
        pwd_bytes = raw_password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        pwd_bytes = raw_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
