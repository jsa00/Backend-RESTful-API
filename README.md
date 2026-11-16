# 게시판 RESTful API

JWT 인증·인가를 적용한 FastAPI 게시판 백엔드 API입니다.
게시판마다 비회원·회원·관리자 권한을 따로 설정할 수 있고, 회원은 본인 글만, 비회원은 작성 시 등록한 비밀번호로만 글을 수정·삭제할 수 있습니다.

- 배포 주소: `http://<EC2 퍼블릭 IP>/docs` (배포 후 갱신)
- API 문서: Swagger UI `/docs`, OpenAPI JSON `/openapi.json`

## 기술 스택

| 구분 | 사용 기술 |
| --- | --- |
| 언어·프레임워크 | Python 3.13, FastAPI, Uvicorn |
| 데이터베이스 | PostgreSQL 17, SQLAlchemy 2 (async) + asyncpg |
| 인증 | JWT (PyJWT, HS512), bcrypt, 토큰 블랙리스트(로그아웃) |
| 검증·문서 | Pydantic v2, OpenAPI(Swagger UI) |
| 패키지 관리 | uv |
| 배포 | Docker, Docker Compose, AWS EC2 |

## 주요 기능

- **회원**: 회원가입, 내 정보 조회, 비밀번호 변경 (bcrypt 해시 저장)
- **인증**: 로그인(JWT 발급), 로그아웃(토큰 블랙리스트), 만료·위조·로그아웃 토큰 차단, 탈퇴 회원 차단
- **게시판(관리자)**: 게시판 생성·수정·삭제, 게시판별 권한 5가지(`ALL` / `USER` / `ADMIN`)와 목록 노출 개수 설정
- **게시글**: 작성·목록(최신순 페이징·검색)·상세(조회수)·수정·삭제, 작성자 본인·관리자·비회원 비밀번호 검증
- **공통**: 모든 응답을 같은 형식(`success / code / message / errors / data / responded_at`)으로 반환, Swagger에 엔드포인트별 에러 코드 문서화, 헬스체크

## 프로젝트 구조

도메인별로 4계층(domain / application / infrastructure / presentation)으로 나누고, 구현체 연결은 `wiring`에서 한곳에 모았습니다.

```text
src/
├── main.py                  # 앱 진입점 (수명주기, 예외 처리기, 의존성 연결, 라우터 등록)
├── shared/core/             # 공통 모듈: DB, 로거, 공통 응답·예외, 전역 예외 처리기, Swagger 에러 문서, 헬스체크
├── user/                    # 회원
├── auth/                    # 인증 (JWT, 블랙리스트)
├── board/                   # 게시판 설정 + 게시글
│   ├── domain/              #   엔티티·값 객체·규칙, 저장소·서비스 인터페이스 (외부 기술에 의존하지 않음)
│   ├── application/         #   유스케이스 (권한 확인 → 엔티티 규칙 → 저장)
│   ├── infrastructure/      #   SQLAlchemy 모델·저장소 구현, bcrypt
│   └── presentation/        #   요청·응답 스키마, 라우터, 의존성 자리(placeholder)
├── wiring/                  # placeholder 의존성에 실제 구현체 연결 (app.dependency_overrides)
└── scripts/promote_admin.py # 관리자 지정 CLI
```

## API 목록

| 메서드 | 경로 | 기능 | 권한 |
| --- | --- | --- | --- |
| POST | `/v1/users` | 회원가입 | 누구나 |
| GET | `/v1/users/me` | 내 정보 조회 | 로그인 |
| PATCH | `/v1/users/me/password` | 비밀번호 변경 | 로그인 |
| POST | `/v1/auth/login` | 로그인 (JWT 발급) | 누구나 |
| POST | `/v1/auth/logout` | 로그아웃 | 로그인 |
| POST | `/v1/boards` | 게시판 생성 | 관리자 |
| GET | `/v1/boards` | 게시판 목록 (`include_deleted`는 관리자) | 누구나 |
| GET | `/v1/boards/{board_id}` | 게시판 조회 | 누구나 |
| PUT | `/v1/boards/{board_id}` | 게시판 설정 수정 | 관리자 |
| DELETE | `/v1/boards/{board_id}` | 게시판 삭제 | 관리자 |
| POST | `/v1/boards/{board_id}/posts` | 게시글 작성 (비회원은 닉네임·비밀번호) | 게시판 글쓰기 권한 |
| GET | `/v1/boards/{board_id}/posts` | 게시글 목록 (`page`, `page_size`, `search_type`, `keyword`) | 게시판 목록 권한 |
| GET | `/v1/posts/{post_id}` | 게시글 상세 (조회수 +1) | 게시판 보기 권한 |
| PUT | `/v1/posts/{post_id}` | 게시글 수정 | 작성자 본인·관리자·비회원 비밀번호 |
| DELETE | `/v1/posts/{post_id}` | 게시글 삭제 (비회원은 `X-Guest-Password` 헤더) | 작성자 본인·관리자·비회원 비밀번호 |
| GET | `/health` | 헬스체크 (DB 연결 확인) | 누구나 |

보호된 API는 Swagger 상단 **Authorize**에 로그인 응답의 `access_token`을 넣으면 바로 테스트할 수 있습니다.

## 실행 방법

### 1. 환경변수

```bash
cp .env.example .env
```

| 이름 | 설명 |
| --- | --- |
| `DATABASE_URL` | 로컬 개발용 DB 주소 (Docker Compose 실행 시에는 `POSTGRES_*`로 자동 생성한 주소가 우선) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Docker Compose의 PostgreSQL 계정 (비밀번호는 `openssl rand -hex 24`) |
| `API_PORT` | Docker Compose로 띄울 때 외부 포트 (기본 80) |
| `JWT_SECRET_KEY` | JWT 서명 키, **필수** (`openssl rand -hex 64`, 없으면 서버가 시작되지 않음) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 액세스 토큰 유효 시간(분, 기본 60) |
| `SQL_ECHO` / `LOGGING_MODE` | SQL 로그 출력 여부 / 로그 레벨(`debug`·`info`) |

### 2-A. 로컬 개발 (uv)

PostgreSQL이 `DATABASE_URL` 주소에 떠 있어야 합니다.

```bash
uv sync
uv run uvicorn main:app --app-dir src --reload
```

### 2-B. Docker Compose (운영과 같은 환경)

앱과 PostgreSQL을 함께 띄웁니다. 테이블은 서버 시작 시 자동으로 만들어집니다.

```bash
docker compose up -d --build
docker compose logs -f api
```

→ `http://localhost/docs` (`API_PORT`를 바꿨다면 그 포트)

### 3. 관리자 지정

회원가입 API는 항상 일반 회원(`USER`)으로 가입합니다. 회원가입 후 서버에서 관리자로 지정합니다.

```bash
# 로컬 개발
uv run python src/scripts/promote_admin.py admin@example.com
# Docker Compose
docker compose exec api python src/scripts/promote_admin.py admin@example.com
```

## EC2 배포

1. **EC2 인스턴스**: Ubuntu, 보안 그룹 인바운드 `22`(내 IP), `80`(전체) 허용
2. **Docker 설치** (Ubuntu)

   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER   # 다시 접속하면 sudo 없이 docker 사용
   ```

3. **코드 받기 + 환경변수**

   ```bash
   git clone https://github.com/jsa00/Backend-RESTful-API.git
   cd Backend-RESTful-API
   cp .env.example .env   # POSTGRES_PASSWORD, JWT_SECRET_KEY 채우기
   ```

4. **배포**

   ```bash
   ./scripts/deploy.sh
   ```

   최신 코드 받기 → 이미지 빌드·컨테이너 교체 → `/health` 통과까지 확인합니다. **재배포도 같은 명령**입니다.

5. **확인**: `http://<퍼블릭 IP>/docs`, 관리자 계정 지정(위 3번)

DB 데이터는 Docker 볼륨(`pgdata`)에 저장돼 재배포해도 유지됩니다. DB 포트(5432)는 외부에 열지 않습니다.
