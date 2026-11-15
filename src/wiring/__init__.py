"""
의존성 와이어링 진입점

도메인별 wire_*_dependencies 함수를 한 번에 호출한다.
main.py는 wire_dependencies(app) 하나만 부르면 모든 도메인의 의존성이 연결된다.
"""

from fastapi import FastAPI
from wiring.auth import wire_auth_dependencies
from wiring.user import wire_user_dependencies


def wire_dependencies(app: FastAPI) -> None:
    """FastAPI dependency_overrides 일괄 와이어링"""
    wire_user_dependencies(app)
    wire_auth_dependencies(app)
    # 도메인별 와이어링 함수를 만들면 여기서 호출한다.
    # wire_board_dependencies(app)
