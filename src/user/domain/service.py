"""
회원 도메인 서비스 인터페이스 (도메인 계층)

비밀번호 해싱은 bcrypt 같은 외부 라이브러리가 필요하지만,
도메인 계층은 외부 기술에 의존하면 안 되므로 "무엇을 하는지"만 추상 메서드로 정의한다.
실제 구현(BcryptPasswordHasher)은 infrastructure/security.py에 있고, wiring에서 주입한다.
→ 나중에 해싱 방식을 바꿔도 도메인 코드는 그대로 둘 수 있다. (의존성 역전, DIP)
"""

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """비밀번호 해싱 도메인 서비스 인터페이스 (구현은 인프라 계층)"""

    @abstractmethod
    def hash(self, raw_password: str) -> str:
        """평문 비밀번호를 단방향 해시값으로 변환"""

    @abstractmethod
    def verify(self, raw_password: str, hashed_password: str) -> bool:
        """평문 비밀번호와 해시값 일치 여부"""
