from fastapi import FastAPI


def wire_dependencies(app: FastAPI) -> None:
    """FastAPI dependency_overrides 일괄 와이어링"""
    # 도메인별 와이어링 함수를 만들면 여기서 호출한다.
    # wire_user_dependencies(app)
    # wire_auth_dependencies(app)
    # wire_board_dependencies(app)
    pass
