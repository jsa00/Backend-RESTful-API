# 게시판 API 운영용 이미지
# - uv로 uv.lock에 고정된 버전 그대로 설치한다. (로컬과 같은 의존성)
# - 운영 모드: --reload 없이 실행하고, root가 아닌 사용자로 실행한다.

FROM python:3.13-slim

# uv 실행 파일만 공식 이미지에서 복사 (로컬과 같은 0.12.10)
COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1) 의존성만 먼저 설치 (소스만 바뀌면 이 단계는 캐시를 재사용해 빌드가 빠르다.)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) 소스 복사
COPY src ./src

# 3) 일반 사용자로 실행
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# --proxy-headers: 앞단 프록시(nginx·로드밸런서)가 있을 때 실제 클라이언트 IP·프로토콜을 사용한다.
CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
