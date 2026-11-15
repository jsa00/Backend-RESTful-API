"""
게시판 도메인 열거형 (도메인 계층)

Role: 게시판 권한 등급
    ALL(0)   비회원 포함 누구나
    USER(1)  로그인 회원 + 관리자
    ADMIN(2) 관리자만
숫자(level)가 클수록 상위 권한이고, 상위 권한은 하위 권한이 허용된 곳을 모두 이용할 수 있다.
예: 게시판 edit_role이 USER면 USER·ADMIN은 글을 쓸 수 있고 비회원(ALL)은 쓸 수 없다.
"""

from enum import StrEnum


class Role(StrEnum):
    """게시판 권한 등급"""

    ALL = "ALL"  # 비회원 포함 모두
    USER = "USER"  # 회원 + 관리자
    ADMIN = "ADMIN"  # 관리자만

    @property
    def level(self) -> int:
        """권한 가중치 (클수록 상위 권한)"""
        return {Role.ALL: 0, Role.USER: 1, Role.ADMIN: 2}[self]

    def satisfies(self, required_role: "Role | str") -> bool:
        """현재 역할이 요구 권한 이상인지 여부"""
        if isinstance(required_role, str):
            required_role = Role(required_role)
        return self.level >= required_role.level
