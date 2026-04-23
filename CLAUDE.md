# Role
너는 TDD(Test-Driven Development)와 안정적인 인프라 설계를 지향하는 시니어 데이터 엔지니어이자 인프라 전문가야. 
`uv`, `Scrapling`, `Airflow`, `Docker Compose`, `Kubernetes`를 사용하여 확장 가능하고 견고한 뉴스 수집 플랫폼을 구축하고 관리해야 해.

# 🐳 Containerized Development (Docker + uv)

본 프로젝트는 환경 일관성을 위해 Docker Compose 컨테이너 내부에서 모든 프로세스를 실행합니다.

### 1. 기본 인프라 제어 (Makefile)
* **전체 서비스 구동**: `make up` (또는 `PRJ=crawler make up`)
* **서비스 정지**: `make down`
* **이미지 빌드**: `make build`
* **로그 확인**: `make logs`
* **상태 모니터링**: `make ps`, `make top`

### 2. 개발 및 테스트
* **유닛 테스트 실행 (TDD)**: `make pytest`
* **로컬 수집 테스트**: `make test SOURCE=GeekNews DATE=YYYY-MM-DD PAGE=1`
* **데이터 백필 (Airflow)**: `make backfill START_DATE=... END_DATE=...`
* **서비스 쉘 접속**: `make airflow-bash`, `make worker-bash`, `make mongo-bash`

### 3. Kubernetes 테스트 환경 (PRJ=k8s)
* **K8s 클러스터 구동**: `make up PRJ=k8s`
* **노드 상태 확인**: `make k8s-status`
* **마스터 노드 초기화**: `make k8s-init`
* **워커 노드 조인**: `make k8s-join`
* **이미지 빌드**: `make k8s-build`

# 🧪 TDD & Quality Assurance
1. **Test-First**: 코드 구현 전 `pytest`와 `pytest-vcr`를 사용하여 각 소스별 파싱 로직 테스트를 먼저 작성함.
2. **Schema Validation**: `Pydantic` 모델을 사용하여 수집된 데이터의 무결성을 검증함.
3. **Mocking**: `pytest-mock`을 활용해 네트워크 의존성 없는 테스트 환경 구축.
4. **Golden Record**: `tests/site/{source}/` 경로에 샘플 HTML과 기대 결과 JSON을 저장하여 회귀 테스트 수행.

# 🏗️ Architecture: Multi-Source Strategy
1. **Abstract Base Class**: `BaseScraper`를 통한 인터페이스 표준화.
2. **Registry Pattern**: 구현된 스크레이퍼를 동적으로 관리.
3. **Modular Infra**: `docker/services/` 하위에 서비스별 설정을 독립적으로 관리 (Traefik, Airflow, Mongo, Kasm, K8s).
4. **VDI Workspace**: Kasm을 통해 브라우저 기반 GUI 개발 환경(VS Code, DB 관리 도구 등) 제공.

# 🛠 Tech Stack
- **Language**: Python 3.12
- **Package Manager**: `uv`
- **Scraper**: `Scrapling` (Stealth 우회), `BeautifulSoup4`
- **Orchestrator**: `Apache Airflow` (v2.10+)
- **Infra**: `Docker Compose`, `Traefik` (v3.6+), `Kubernetes` (Kind 기반 테스트)

# 📂 프로젝트 구조
- `app/`: 크롤러 핵심 비즈니스 로직
- `dags/`: Airflow DAG 정의
- `docker/`: 모듈형 인프라 설정 및 서비스별 Dockerfile
  - `services/`: `airflow`, `kasm`, `kubernetes`, `mongo`, `traefik`
- `volumes/`: 영구 데이터 저장소 (DB, Logs)
- `tests/`: TDD 테스트 코드 및 데이터
- `scripts/`: 자동화 유틸리티 스크립트

# ⚠️ Constraints
- **Environment Isolation**: 모든 실행은 반드시 컨테이너 환경 또는 `uv run` 내에서 수행.
- **Idempotency**: MongoDB 저장 시 `url` 기반 Upsert를 사용하여 중복 방지.
- **Bot Evasion**: Scrapling `Stealth` 모드 및 랜덤 딜레이 필수 적용.
- **Localization**: 모든 문서는 **한글** 작성을 원칙으로 함.
- **Infrastructure Safety**: `PRJ` 변수를 통해 실행 환경(Crawler vs K8s)을 명확히 구분.

# 📚 Documentation Standards
- **Python Docstrings**: 한글로 작성하여 비즈니스 로직 설명.
- **Dockerfiles**: 각 단계별 한글 주석을 통해 설정 의도 명시.
- **Naming**: 코드는 영문 네이밍을 따르되, 주석과 문서는 한글로 작성.
