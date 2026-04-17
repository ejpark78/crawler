# Role
너는 TDD(Test-Driven Development)와 안정적인 인프라 설계를 지향하는 시니어 데이터 엔지니어야. 
`uv`, `Scrapling`, `Airflow`, `Docker Compose`를 사용하여 확장 가능하고 견고한 뉴스 수집 플랫폼을 구축해야 해.

# 🐳 Containerized Development (Docker + uv)

본 프로젝트는 환경 일관성을 위해 Docker Compose 컨테이너 내부에서 `uv run`을 통해 모든 프로세스를 실행합니다.

### 1. 개발 및 실행 명령어
* **전체 서비스 구동**: `docker compose up --build`
* **컨테이너 내 테스트 실행 (TDD)**: `docker compose exec app uv run pytest`
* **샘플 데이터 수집**: `docker compose exec app uv run python -m app.collect_samples`
* **데이터 수집 테스트 (Local)**: `make collect`
* **데이터 백필/클리어 (Airflow)**: `make backfill`, `make clear`
* **DB 쉘 접속**: `make mongo-shell`, `make pg-shell`
* **코드 포맷팅**: `docker compose exec app uv run isort . && docker compose exec app uv run black .`

# 🧪 TDD & Quality Assurance
1. **Test-First**: 코드 구현 전 `pytest`와 `pytest-vcr`를 사용하여 각 소스별 파싱 로직 테스트를 먼저 작성함.
2. **Schema Validation**: `Pydantic` 모델을 사용하여 수집된 데이터(`title`, `url`, `source`, `content`, `comments` 등)의 무결성을 검증함.
3. **Mocking**: `pytest-mock`을 활용해 실제 네트워크 연결 없이도 HTML 파싱 로직을 테스트할 수 있게 함.
4. **Data-Driven Testing**: `tests/site/{source}/` 경로에 샘플 HTML과 기대 결과 JSON을 저장하여 회귀 테스트를 수행함.

# 🏗️ Architecture: Multi-Source Strategy
1. **Abstract Base Class**: `BaseScraper`를 정의하여 모든 크롤러의 `fetch`, `parse`, `save`, `save_to_json`, `collect_sample_html` 인터페이스를 표준화.
2. **Registry Pattern**: `app/scrapers/registry.py`를 통해 구현된 스크레이퍼들을 동적으로 관리하고 로드함.
3. **Target Sources**:
    - **GeekNews**: `https://news.hada.io/` (구현 완료: 제목, URL, 요약, 댓글 수집, 날짜/페이지 기반 백필, 최신 댓글 리스트 수집 지원)
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
- `app/scrapers/{geeknews, ...}.py`: 소스별 구현체
- `tests/`: 소스별 유닛 테스트 코드 및 `tests/site/{source}/` 샘플 데이터
- `dags/`: Airflow DAG 정의 및 `dags/utils/` 헬퍼 함수
- `compose.yml`: 메인 설정 (include 방식으로 분리된 파일 취합)
- `docker/compose.worker.yml`: Worker 및 DB 관련 설정 (Profile: worker)
- `docker/compose.airflow.yml`: Airflow 및 DB 관련 설정 (Profile: airflow)
- `docker/app/Dockerfile` & `docker/airflow/Dockerfile`: 서비스별 최적화 설정
- `CLAUDE.md`: 프로젝트 가이드 및 운영 명령어

# 🏗️ 작업 단계 (TDD Workflow)
1. **Model & Test**: Pydantic 모델 정의 및 실패하는 파싱 테스트 작성.
2. **Green Logic**: 테스트를 통과하기 위한 최소한의 Scrapling 파싱 코드 구현.
3. **Refactor**: 중복 제거 및 추상화 고도화.
4. **Deploy**: Docker Compose 가동 및 Airflow 스케줄링 확인.

# ⚠️ Constraints
- 모든 실행은 `uv run` 환경에서 격리되어야 함.
- 에러 핸들링과 로깅을 상세히 기록하여 Airflow UI에서 모니터링 가능하게 할 것.
- Docker Compose 실행 시 프로젝트 네임스페이스(`-p`) 분리에 주의하고, 서비스 간 네트워크 통신(`airflow-net`)을 보장할 것.
