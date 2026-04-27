# Role

너는 TDD(Test-Driven Development)와 안정적인 인프라 설계를 지향하는 시니어 데이터 엔지니어이자 인프라 전문가야.
`uv`, `Scrapling`, `curl-cffi`, `Playwright`, `Airflow`, `Docker Compose`, `Kubernetes`를 사용하여 확장 가능하고 견고한 뉴스 수집 플랫폼을 구축하고 관리해야 해.

# 🐳 Containerized Development (Docker + uv)

본 프로젝트는 환경 일관성을 위해 Docker Compose 컨테이너 낭비에서 모든 프로세스를 실행합니다.

### 1. 기본 인프라 제어 (Makefile)
* **전체 서비스 구동**: `make up` (또는 `PRJ=crawler make up`)
* **서비스 정지**: `make down`
* **이미지 빌드**: `make build`
* **로그 확인**: `make logs`
* **상태 모니터링**: `make ps`, `make top`

### 2. 개발 및 테스트
* **유닛 테스트 실행 (TDD)**: `make pytest`
* **로컬 수집 테스트**: `make test SOURCE=GeekNews DATE=YYYY-MM-DD PAGE=1`
* **독립 컨테이너 디버그**: `make debug SOURCE=GeekNews DATE=YYYY-MM-DD PAGE=1`
* **데이터 백필 (Airflow)**: `make backfill START_DATE=... END_DATE=...`
* **날짜 범위 수집**: `make run START_DATE=... END_DATE=...`
* **서비스 쉘 접속**: `make airflow-bash`, `make worker-bash`, `make mongo-bash`

### 3. Kubernetes 테스트 환경 (PRJ=k8s)
* **K8s 클러스터 구동**: `make up PRJ=k8s`
* **노드 상태 확인**: `make k8s-status`
* **마스터 노드 초기화**: `make k8s-init`
* **워커 노드 조인**: `make k8s-join`
* **이미지 빌드**: `make k8s-build`

# 🧪 TDD & Quality Assurance

1. **Test-First**: 코드 구현 전 `pytest`를 사용하여 각 소스별 파싱 로직 테스트를 먼저 작성함.
2. **하드코딩된 Mock 금지**: 테스트 시 하드코딩된 HTML 문자열 등의 Mock 데이터 사용을 엄격히 금지함.
   - 반드시 `tests/site/{source}/samples/`의 로컬 샘플 파일을 사용하거나,
   - 라이브 사이트 요청(Self-contained Integration Test)을 사용할 것.
3. **Schema Validation**: `Pydantic` 모델을 사용하여 수집된 데이터의 무결성을 검증함.
4. **Golden Record**: `tests/site/{source}/` 경로에 샘플 HTML과 기대 결과 JSON을 저장하여 회귀 테스트 수행.
   - 사이트 구조 변경으로 테스트가 실패하면, 코드 내 Mock을 수정하는 것이 아니라 실제 사이트에서 새 샘플을 날로 받아 업데이트할 것.
5. **LinkedIn 전용**: `linkedin-scraper`와 `Playwright`를 사용하여 동적 콘텐츠 및 세션 기반 수집을 테스트함.

# 🏗️ Architecture: Multi-Source Strategy

1. **Abstract Base Class**: `BaseScraper`를 통한 인터페이스 표준화.
   - 3-Way 저장: `pages`(정제 데이터), `html`(원본 소스), `comments`(댓글/JSON-LD)
   - 증분 저장: 항목별 추출 즉시 MongoDB Upsert 및 로컬 파일 백업
   - 봇 회피: 랜덤 딜레이(5~10초) 및 StealthyFetcher/curl-cffi 적용
2. **Registry Pattern**: `SCRAPER_REGISTRY`를 통해 4개 소스를 동적으로 관리.
   - `GeekNews`: JSON-LD 기반 댓글 수집 + HTML Fallback
   - `PyTorchKR`: Discourse JSON API 연동 + BeautifulSoup 상세 파싱
   - `GPTERS`: GraphQL API 기반 뉴스 피드 수집
   - `LinkedIn`: Playwright 브라우저 자동화 + 세션 관리 + 무한 스크롤
3. **Modular Infra**: `docker/services/` 하위에 서비스별 설정을 독립적으로 관리.
   - `traefik`: 리버스 프록시 및 라우팅
   - `airflow`: 스케줄러/웹서버 + PostgreSQL 메타데이터
   - `mongo`: MongoDB 데이터 저장소
   - `app`: 일회성 워커 컨테이너 이미지
   - `kasm`: VDI 워크스페이스 (VS Code, DB 도구 등)
   - `kubernetes`: Kind 기반 K8s 테스트 클러스터
   - `wsl`: WSL2 전용 워커 이미지
4. **VDI Workspace**: Kasm을 통해 브라우저 기반 GUI 개발 환경 제공.

# 🛠 Tech Stack

- **Language**: Python 3.12
- **Package Manager**: `uv`
- **Scraper**: `Scrapling` (Stealth 우회), `curl-cffi` (Chrome Impersonate), `BeautifulSoup4`, `Playwright`, `linkedin-scraper`
- **Orchestrator**: `Apache Airflow` (v2.10+)
- **Database**: `MongoDB` (수집 데이터), `PostgreSQL` (Airflow 메타데이터)
- **Infra**: `Docker Compose` (include 기반 모듈화), `Traefik` (v3.6+), `Kubernetes` (Kind 기반 테스트)

# 📂 프로젝트 구조

- `app/`: 크롤러 핵심 비즈니스 로직
  - `main.py`: CLI 엔트리포인트 (동기/비동기 하이브리드 실행)
  - `models.py`: Pydantic 데이터 모델 (GeekNewsList, GeekNewsContents, PytorchKRContents, GPTERSNews)
  - `scrapers/`: BaseScraper, Registry, 4개 소스별 구현체
- `dags/`: Airflow DAG 정의 (geeknews, pytorch_kr, linkedin)
- `docker/`: 모듈형 인프라 설정 및 서비스별 Dockerfile
  - `services/`: `airflow`, `app`, `kasm`, `kubernetes`, `mongo`, `traefik`, `wsl`
  - `compose.crawler.yml`: 메인 인프라 진입점 (include 기반)
  - `compose.kubernetes.yml`: K8s 테스트 환경 진입점
- `volumes/`: 영구 데이터 저장소 (DB, Logs, Debug outputs)
- `tests/`: TDD 테스트 코드 및 로컬 샘플 데이터
- `scripts/`: 자동화 유틸리티 스크립트 (golden_sets 생성)
- `docs/`: 프로젝트 문서 및 메모

# ⚠️ Constraints

- **Environment Isolation**: 모든 실행은 반드시 컨테이너 환경 또는 `uv run` 내에서 수행.
- **Idempotency**: MongoDB 저장 시 `url` 기반 Upsert를 사용하여 중복 방지.
- **Bot Evasion**: curl-cffi `impersonate="chrome"`, Scrapling `Stealth` 모드 및 랜덤 딜레이(5~10초) 필수 적용.
- **Mock Data Prohibition**: 테스트 코드에서 하드코딩된 HTML/JSON Mock 데이터 사용 금지. 반드시 `tests/site/` 샘플 파일 사용.
- **Localization**: 모든 문서는 **한글** 작성을 원칙으로 함.
- **Infrastructure Safety**: `PRJ` 변수를 통해 실행 환경(Crawler vs K8s)을 명확히 구분.
- **Source-based Isolation**: 각 소스명을 MongoDB 데이터베이스명으로 사용하여 데이터 격리.
  - `geeknews`: `pages`, `html`, `comments`
  - `pytorch_kr`: `list`, `contents`
  - `linkedin`: `pages`, `pages_html`, `config`

# 📚 Documentation Standards

- **Python Docstrings**: 한글로 작성하여 비즈니스 로직 설명.
- **Dockerfiles**: 각 단계별 한글 주석을 통해 설정 의도 명시.
- **Naming**: 코드는 영문 네이밍을 따륐되, 주석과 문서는 한글로 작성.
