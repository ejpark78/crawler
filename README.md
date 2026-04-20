# 🌐 News Collection Platform

TDD(Test-Driven Development)와 확장 가능한 아키텍처를 기반으로 구축된 AI 및 기술 뉴스 수집 플랫폼입니다. `uv`, `Scrapling`, `Airflow`, `Docker Compose`를 사용하여 견고한 데이터 파이프라인을 제공합니다.

## 🚀 주요 특징

- **Multi-Source Strategy**: `BaseScraper` 추상 클래스와 Registry 패턴을 통해 신규 뉴스 소스를 쉽고 빠르게 추가할 수 있는 구조입니다.
- **TDD 기반 품질 보증**: `pytest-vcr`과 Golden Record 방식을 사용하여 네트워크 의존성 없는 빠른 회귀 테스트를 수행합니다.
- **강력한 수집 능력**: `Scrapling`의 Stealth 모드를 통해 봇 탐지를 우회하며, 단순 리스트 수집을 넘어 상세 페이지의 본문과 댓글까지 수집하는 Deep Collection을 지원합니다.
- **안정적인 오케스트레이션**: `Apache Airflow`를 통해 수집 스케줄링 및 과거 데이터 소급 수집(Backfill)을 관리합니다.
- **데이터 무결성**: `Pydantic` 모델을 통한 스키마 검증과 MongoDB의 Upsert 로직을 통해 데이터 중복을 방지하고 멱등성을 보장합니다.

## 🛠 기술 스택

- **Language**: Python 3.12
- **Package Manager**: `uv`
- **Scraping**: `Scrapling`, `BeautifulSoup4`
- **Orchestrator**: `Apache Airflow`
- **Database**: `MongoDB`
- **Infrastructure**: `Docker Compose`, `Traefik`

## 📂 프로젝트 구조

```text
.
├── app/
│   ├── main.py              # 애플리케이션 진입점
│   ├── models.py            # Pydantic 데이터 모델
│   └── scrapers/           # 스크레이퍼 구현체 및 베이스 클래스
│       ├── base.py          # 추상 베이스 클래스
│       ├── registry.py      # 스크레이퍼 등록 관리
│       └── {source}.py      # 소스별 수집 로직
├── dags/                    # Airflow DAG 정의 파일
├── docker/                  # 서비스별 Dockerfile 및 설정
├── scripts/                 # 테스트 데이터(Golden Set) 생성 스크립트
├── tests/                   # 유닛 테스트 및 사이트별 샘플 HTML/JSON
└── compose.yml             # 인프라 구성 파일
```

## ⚙️ 설치 및 실행

### 1. 환경 설정
본 프로젝트는 Docker 환경에서 실행됩니다. 필요한 설정을 완료한 후 다음 명령어로 서비스를 구동하십시오.

```bash
docker compose up -d
```

### 2. 주요 실행 명령어 (Makefile 활용)
- **테스트 실행**: `make unittest`
- **로컬 수집 테스트**: `make test DATE=YYYY-MM-DD PAGE=1`
- **데이터 백필**: `make backfill`
- **DB 접속**: `make mongo-bash` 또는 `make pgsql`
- **서비스 쉘 접속**: `make worker-bash` 또는 `make airflow-bash`

## 🧪 개발 워크플로우 (TDD)

신규 소스 추가 시 다음 단계를 권장합니다:
1. **Model & Test**: `app/models.py`에 모델 정의 및 `tests/`에 실패하는 테스트 작성.
2. **Green Logic**: 테스트를 통과하는 최소한의 파싱 로직 구현.
3. **Golden Record**: `scripts/`의 생성 스크립트를 통해 실제 데이터를 JSON 기대값으로 저장.
4. **Refactor**: 코드 최적화 및 추상화.
5. **Deploy**: Airflow DAG 설정 및 스케줄링 확인.

## 📝 라이선스
[LICENSE](./LICENSE) 파일을 참조하십시오.
