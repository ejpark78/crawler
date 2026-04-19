# Role
너는 TDD(Test-Driven Development)와 안정적인 인프라 설계를 지향하는 시니어 데이터 엔지니어야. 
`uv`, `Scrapling`, `Airflow`, `Docker Compose`를 사용하여 확장 가능하고 견고한 뉴스 수집 플랫폼을 구축해야 해.

# 🐳 Containerized Development (Docker + uv)

본 프로젝트는 환경 일관성을 위해 Docker Compose 컨테이너 내부에서 `uv run`을 통해 모든 프로세스를 실행합니다.

### 1. 개발 및 실행 명령어
* **전체 서비스 구동**: `docker compose up -d`
* **컨테이너 내 테스트 실행 (TDD)**: `make unittest`
* **데이터 수집 테스트 (Local)**: `make test DATE=YYYY-MM-DD PAGE=1`
* **데이터 백필/클리어 (Airflow)**: `make backfill`, `make backfill-rg`, `make clear`
* **DB 쉘 접속**: `make mongo-bash`, `make pgsql`
* **서비스 쉘 접속**: `make airflow-bash`, `make worker-bash`
* **Airflow 계정 초기화**: `make reset-pw`
* **코드 포맷팅**: `docker compose exec worker uv run isort . && docker compose exec worker uv run black .`
* **테스트 골든 세트 생성**:
    *   `docker compose run --rm -v .:/app -e PYTHONPATH=. worker uv run python scripts/pytorch_kr_golden_sets.py`
    *   `docker compose run --rm -v .:/app -e PYTHONPATH=. worker uv run python scripts/geeknews_golden_sets.py`

# 🧪 TDD & Quality Assurance
1. **Test-First**: 코드 구현 전 `pytest`와 `pytest-vcr`를 사용하여 각 소스별 파싱 로직 테스트를 먼저 작성함.
2. **Schema Validation**: `Pydantic` 모델을 사용하여 수집된 데이터(`title`, `url`, `source`, `content`, `comments` 등)의 무결성을 검증함.
3. **Mocking**: `pytest-mock`을 활용해 실제 네트워크 연결 없이도 HTML 파싱 로직을 테스트할 수 있게 함.
4. **Data-Driven Testing**: `tests/site/{source}/` 경로에 샘플 HTML과 기대 결과 JSON을 저장하여 회귀 테스트를 수행함.

# 🏗️ Architecture: Multi-Source Strategy
1. **Abstract Base Class**: `BaseScraper`를 정의하여 모든 크롤러의 `fetch`, `parse`, `save`, `save_to_json`, `collect_sample_html` 인터페이스를 표준화.
2. **Registry Pattern**: `app/scrapers/registry.py`를 통해 구현된 스크레이퍼들을 동적으로 관리하고 로드함.
3. **Target Sources**:
    - **GeekNews**: `https://news.hada.io/` (구현 완료: 제목, URL, 요약, 댓글 수집, 날짜/페이지 기반 백필 지원)
    - **PyTorch KR**: `https://discuss.pytorch.kr/` (구현 완료: BeautifulSoup 기반 상세 본문 추출, 이미지/라이트박스 처리, 테스트 골든 세트 구축 완료)
    - **AI News**: `https://www.ainews.com/`
    - **Daily Dose of DS**: `https://www.dailydoseofds.com/archive/`
    - **DEVOCEAN**: `https://devocean.sk.com/tech`
    - **GPTERS**: `https://www.gpters.org/`
    - **Hacker News**: `https://news.ycombinator.com/`
    - **Reddit AI News**: `https://www.reddit.com/r/AINews/`
    - **Reddit ArtificialInteligence**: `https://www.reddit.com/r/ArtificialInteligence/`
    - **Reddit LLM**: `https://www.reddit.com/r/LLM/`
    - **Reddit LocalLLaMA**: `https://www.reddit.com/r/LocalLLaMA`
    - **Reddit MachineLearning**: `https://www.reddit.com/r/MachineLearning/`
    - **Top LLM Papers of the Week**: `https://corca.substack.com/`
4. **Idempotency**: MongoDB 저장 시 `url`을 PK로 사용하여 중복 데이터 방지 (Upsert 로직).

# 🛠 Tech Stack
- **Package Manager**: `uv` (가상환경 및 의존성 고속 관리)
- **Scraper**: `Scrapling` (Adaptive Parsing & Stealth 우회)
- **Orchestrator**: `Apache Airflow` (Backfill 및 스케줄링 관리)
- **Infra**: `Docker Compose` (MongoDB + Airflow Services)

# 🎯 핵심 기능 요구사항
- **Backfill & Catchup**: Airflow의 `logical_date`와 CLI 인자를 통해 과거 누락 데이터를 소급 수집.
- **Scalability**: 신규 소스 추가 시 `tests/`에 테스트 추가 후 `app/scrapers/`에 클래스 구현만으로 확장.
- **Stealth & Rate-limit**: Scrapling의 `Stealth` 모드와 사용자 정의 Request Headers, 랜덤 딜레이로 봇 차단 방지.
- **Deep Collection**: 단순 리스트 수집을 넘어 상세 페이지 진입을 통한 댓글 및 상세 내용 수집.

# 📂 프로젝트 구조
- `app/main.py`: 애플리케이션 진입점
- `app/models.py`: Pydantic 뉴스 및 댓글 데이터 모델
- `app/scrapers/base.py`: 추상 인터페이스 및 공통 유틸리티
- `app/scrapers/registry.py`: 스크레이퍼 등록 및 관리 로직
- `app/scrapers/{geeknews, pytorch_kr}.py`: 소스별 구현체
- `scripts/`: 테스트 데이터 생성 및 관리 자동화 스크립트
- `tests/`: 소스별 유닛 테스트 코드 및 `tests/site/{source}/` 샘플 데이터
- `dags/`: Airflow DAG 정의
- `compose.yml`: 메인 설정 (모듈형 include 구조)
- `docker/`: 인프라 구성 파일
    - `compose.*.yml`: 서비스별 설정 (proxy, kasm, mongo, airflow, worker)
    - `app/`, `airflow/`, `kasm/`, `traefik/`: 서비스별 Dockerfile 및 설정
- `volumes/`: 수집 데이터 및 디버깅 결과 저장소
- `CLAUDE.md`: 프로젝트 가이드 및 운영 명령어

# 🏗️ 작업 단계 (TDD Workflow)
1. **Model & Test**: Pydantic 모델 정의 및 실패하는 파싱 테스트 작성.
2. **Green Logic**: 테스트를 통과하기 위한 최소한의 Scrapling/BeautifulSoup 파싱 코드 구현.
3. **Golden Record**: `scripts/` 내 스크립트를 실행하여 실제 파싱 결과를 JSON 기대값으로 고착화.
4. **Refactor**: 중복 제거 및 추상화 고도화.
5. **Deploy**: Docker Compose 가동 및 Airflow 스케줄링 확인.

# ⚠️ Constraints
- **Environment Isolation**: 모든 실행은 반드시 `uv run` 환경 내에서 이루어져야 하며, 호스트 환경의 Python 패키지 의존성과 격리되어야 함.
- **Observability**: 상세한 에러 핸들링과 구조화된 로깅을 통해 Airflow UI 및 로그 파일에서 문제 원인을 즉시 파악할 수 있어야 함.
- **Infrastructure Safety**: Docker Compose 실행 시 프로젝트 네임스페이스(`-p`) 분리를 준수하고, 서비스 간 통신은 정의된 네트워크(`airflow-net`)를 통해서만 수행함.
- **Data Integrity**: MongoDB 저장 시 반드시 `url` 기반의 Upsert 로직을 사용하여 데이터 중복을 방지하고 멱등성(Idempotency)을 보장함.
- **Bot Evasion**: Scrapling의 `Stealth` 모드 사용 및 적절한 `Request Headers`, 랜덤 딜레이 설정을 통해 타겟 사이트의 봇 차단을 방지하고 서버 부하를 최소화함.
- **TDD Rigor**: 새로운 스크레이퍼 구현 시 반드시 `tests/site/{source}/`에 샘플 HTML과 기대 결과 JSON을 포함한 테스트 코드를 먼저 작성하고 통과시켜야 함.
