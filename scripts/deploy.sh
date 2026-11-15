#!/usr/bin/env bash
# 배포·재배포 스크립트 (EC2 서버에서 프로젝트 루트 기준으로 실행)
#   ./scripts/deploy.sh
# 1) 최신 코드 받기 → 2) 이미지 다시 빌드 후 컨테이너 교체 → 3) 헬스체크 통과 확인
# 처음 배포할 때는 .env를 먼저 만들어야 한다. (README의 EC2 배포 참고)

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "[실패] .env 파일이 없습니다. cp .env.example .env 후 값을 채워주세요." >&2
  exit 1
fi

# .env에서 API_PORT만 읽기 (없으면 80)
API_PORT=$(grep -E '^API_PORT=' .env | head -n1 | cut -d= -f2 | cut -d'#' -f1 | tr -d ' "' || true)
API_PORT=${API_PORT:-80}

echo "[1/3] 최신 코드 받기"
git pull --ff-only

echo "[2/3] 이미지 빌드 및 컨테이너 교체"
docker compose up -d --build
docker image prune -f > /dev/null

echo "[3/3] 헬스체크 (http://localhost:${API_PORT}/health)"
for _ in $(seq 1 30); do
  if curl -fsS "http://localhost:${API_PORT}/health" > /dev/null; then
    echo "[완료] 배포 성공 - Swagger: http://<퍼블릭 IP>:${API_PORT}/docs"
    exit 0
  fi
  sleep 2
done

echo "[실패] 헬스체크가 60초 안에 통과하지 않았습니다. 최근 로그:" >&2
docker compose logs --tail 50 api >&2
exit 1
