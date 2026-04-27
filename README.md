# 🌐 News Collection for RAG

TDD(Test-Driven Development)와 확장 가능한 아키텍처를 기반으로 구축된 AI 및 기술 뉴스 수집 플랫폼입니다. `uv`, `Scrapling`, `Airflow`, `Docker Compose`를 사용하여 견고한 데이터 파이프라인을 제공합니다.

## 시스템 아키텍처

![System Architecture](./docs/assets/system_architecture.png)

```text
==============================================================================
                    NEWS CRAWLER SYSTEM ARCHITECTURE
==============================================================================

                          [ External Users ]
                                   │
               ▼ (af.localhost, pg.localhost, me.localhost)
                       ┌───────────────────┐
                       │  Traefik Proxy    │ (Edge Gateway)
                       └─────────┬─────────┘
                                 │
     ┌───────────────────────────┴────────────────────────────┐
     │              Docker Network: crawler_default           │
     └────────┬──────────────────┬───────────────────┬────────┘
              │                  │                   │
              ▼                  │                   ▼
      ┌─────────────┐            │            ┌─────────────┐
      │ Airflow Web │            │            │  Kasm (VDI) │
      └──────┬──────┘            │            │  (Optional) │
             │                   │            └─────────────┘
             │           ┌───────▼───────┐
             │           │  Airflow Sch  │ (Scheduler)
             │           └───────┬───────┘
             │                   │
             │                   │ 🚀 (1) Trigger via /var/run/docker.sock
             │                   │
             │                   ▼
             │           ┌───────────────┐
             │           │    Worker     │ (Ephemeral Container)
             │           └───────┬───────┘
             ▼                   │ 💾 (2) Save Scraped Data
      ┌─────────────┐            ▼            ┌─────────────┐
      │  PostgreSQL │            ─────────────▶   MongoDB   │
      │ (Meta Data) │                         │  (Scraped)  │
      └──────┬──────┘                         └──────┬──────┘
             │                                       │
      ───────┼───────────────────────────────────────┼───────
             ▼                                       ▼
      ┌─────────────┐                         ┌─────────────┐
      │  Volume:    │                         │  Volume:    │
      │  /postgres  │                         │  /mongodb   │
      └─────────────┘                         └─────────────┘

==============================================================================
```

```text
==============================================================================
                  KASM INTERACTIVE MANAGEMENT FLOW
==============================================================================

      [ Developer Access ]
              │
              ▼ (kasm.localhost)
      ┌───────────────────┐
      │  Traefik Proxy    │
      └─────────┬─────────┘
                │
    ┌───────────┴────────────────────────────────────────┐
    │          Docker Network: crawler_default           │
    └──────────────────────────┬─────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │       Kasm (VDI Workspace)      │
              │  ┌───────────────────────────┐  │
              │  │  💻 VS Code (Dev)         │──┼──▶ [ Code/Debug ]
              │  │  🐘 DBeaver (SQL)         │──┼──▶ [ PostgreSQL ]
              │  │  🍃 Mongo-Comp (NoSQL)    │──┼──▶ [ MongoDB    ]
              │  │  🌐 Chrome (Web UI)       │──┼──▶ [ Airflow UI ]
              │  └───────────────────────────┘  │
              └─────────────────────────────────┘

==============================================================================
```

1.  **Entry Point**: 외부 사용자가 `Traefik` 프록시를 통해 시스템에 접속합니다.
2.  **Shared Network**: 모든 서비스가 `crawler_default` 가상 네트워크를 통해 상호 통신합니다.
3.  **Control Center**: `Airflow`가 시스템의 중심에서 크롤링 태스크를 스케줄링하고 워커를 트리거합니다.
4.  **Worker**: Airflow Scheduler에 의해 동적으로 생성되는 일회성(Ephemeral) 컨테이너로, 실제 수집 작업을 수행합니다.
5.  **Kasm (VDI)**: 브라우저 기반 GUI 개발 환경을 제공하여 데이터 확인 및 코드 수정을 인터랙티브하게 수행할 수 있습니다. (현재 `compose.crawler.yml`에서 주석 처리됨)
6.  **Persistence Layer**: 컨테이너가 삭제되어도 데이터가 유지되는 호스트의 `Volume` 영역을 활용합니다.


## 🚀 주요 특징

- **Multi-Source Strategy**: `BaseScraper` 추상 클래스와 Registry 패턴을 통해 신규 뉴스 소스를 유연하게 추가합니다.
  - 지원 소스: [GeekNews](https://news.hada.io), [PyTorch KR](https://discuss.pytorch.kr), [GPTERS](https://www.gpters.org/news), [LinkedIn](https://www.linkedin.com)
- **TDD 기반 품질 보증**: `pytest`와 로컬 샘플 파일 기반의 Golden Record 방식을 사용하여 네트워크 의존성 없는 테스트를 수행합니다. 하드코딩된 Mock 데이터 사용을 엄격히 금지합니다.
- **강력한 수집 능력**: 
  - `curl-cffi` (Chrome Impersonate)를 통한 봇 탐지 우회
  - `Scrapling` Stealth 모드 및 `Playwright`(LinkedIn)를 통한 동적 콘텐츠 수집
  - 상세 페이지까지 심층 수집 (댓글, JSON-LD)
- **안정적인 오케스트레이션**: `Apache Airflow`를 통해 수집 스케줄링 및 Backfill을 관리합니다. Dynamic Task Mapping으로 다중 페이지를 병렬 처리합니다.
- **데이터 무결성**: `Pydantic` 모델 검증과 MongoDB Upsert 로직을 통해 데이터 멱등성을 보장합니다.
- **3-Way 멀티 레이어 저장**: 수집된 데이터를 `pages`(정제 데이터), `html`(원본 소스), `comments`(댓글/JSON-LD) 컬렉션에 분리 저장합니다.

## 🛠 기술 스택

- **Language**: Python 3.12
- **Package Manager**: `uv`
- **Scraping**: `Scrapling`, `curl-cffi`, `BeautifulSoup4`, `Playwright`, `linkedin-scraper`
- **Orchestrator**: `Apache Airflow` (v2.10+)
- **Database**: `MongoDB` (수집 데이터), `PostgreSQL` (Airflow 메타데이터)
- **Infrastructure**: `Docker Compose` (include 기반 모듈화), `Traefik` (v3.6+), `Kubernetes` (Kind 기반 테스트 환경)

## 📂 프로젝트 구조

```text
.
├── app/                         # 크롤러 애플리케이션 소스
│   ├── main.py                  # CLI 진입점 (동기/비동기 하이브리드 실행)
│   ├── models.py                # Pydantic 데이터 모델 (GeekNews, PyTorchKR, GPTERS, LinkedIn)
│   └── scrapers/                # 소스별 스크레이퍼 구현체
│       ├── base.py              # BaseScraper 추상 클래스 (3-Way 저장, Upsert)
│       ├── registry.py          # 스크레이퍼 레지스트리 (4개 소스 등록)
│       ├── geeknews.py          # GeekNews 스크레이퍼 (JSON-LD + HTML Fallback)
│       ├── pytorch_kr.py        # PyTorch KR 스크레이퍼 (Discourse JSON API)
│       ├── gpters.py            # GPTERS 스크레이퍼 (GraphQL API)
│       └── linkedin.py          # LinkedIn 스크레이퍼 (Playwright 브라우저 자동화)
├── dags/                        # Airflow DAG 정의
│   ├── geeknews_dag.py          # GeekNews 수집 DAG (Dynamic Task Mapping, 3페이지 병렬)
│   ├── pytorch_kr_dag.py        # PyTorchKR 수집 DAG (Dynamic Task Mapping)
│   └── linkedin_dag.py          # LinkedIn 수집 DAG (Playwright 세션 기반)
├── docker/                      # 모듈형 인프라 설정
│   ├── services/                # 서비스별 Dockerfile 및 독립 compose.yml
│   │   ├── airflow/             # Airflow + PostgreSQL + pgAdmin
│   │   ├── app/                 # 크롤러 워커 이미지 (일회성 실행)
│   │   ├── kasm/                # Kasm VDI 모듈 (Ubuntu GUI, 한글 입력)
│   │   ├── kubernetes/          # K8s 테스트 환경 모듈 (Kind 기반)
│   │   ├── mongo/               # MongoDB + Mongo Express
│   │   ├── traefik/             # Traefik 리버스 프록시
│   │   └── wsl/                 # WSL 환경용 워커 이미지
│   ├── compose.crawler.yml      # 메인 인프라 진입점 (include 기반)
│   ├── compose.kubernetes.yml   # K8s 환경 테스트 진입점
│   └── README.md                # Docker 인프라 상세 가이드
├── scripts/                     # 테스트 데이터 생성 유틸리티 (golden_sets)
├── tests/                       # 유닛 테스트 및 샘플 데이터
│   ├── test_geeknews.py         # GeekNews 파싱 테스트 (샘플 파일 기반)
│   ├── test_pytorch_kr.py       # PyTorchKR 파싱 테스트 (Golden Record)
│   └── site/                    # 로컬 샘플 HTML/JSON 저장소
├── docs/                        # 프로젝트 문서 및 메모
├── Makefile                     # 통합 관리 명령어
├── compose.yml                  # 기본 실행 설정 (docker/compose.crawler.yml include)
├── pyproject.toml               # Python 프로젝트 설정 (uv)
└── uv.lock                      # 의존성 잠금 파일
```

## ⚙️ 설치 및 실행

### 1. 기본 인프라 실행 (Crawler Stack)
```bash
make up
```

### 2. Kubernetes 테스트 환경 실행
```bash
make up PRJ=k8s
```

### 3. 주요 관리 명령어 (Makefile)

| 명령어 | 설명 |
|--------|------|
| `make up` | 전체 서비스 기동 (Airflow, MongoDB, Traefik 등) |
| `make down` | 전체 서비스 정지 |
| `make build` | Docker 이미지 빌드 |
| `make ps` | 컨테이너 상태 실시간 모니터링 |
| `make top` | 컨테이너 리소스 사용량 실시간 모니터링 |
| `make pytest` | 유닛 테스트 실행 (TDD) |
| `make test SOURCE=GeekNews DATE=YYYY-MM-DD PAGE=1` | 로컬 수집 테스트 |
| `make debug SOURCE=GeekNews DATE=YYYY-MM-DD PAGE=1` | 독립 컨테이너 디버그 실행 |
| `make backfill START_DATE=... END_DATE=...` | Airflow Backfill (날짜 범위 소급 수집) |
| `make run START_DATE=... END_DATE=...` | 날짜 범위 반복 수집 (1~5페이지) |
| `make logs` | 컨테이너 로그 확인 |
| `make k8s-status` | K8s 노드 상태 확인 |
| `make k8s-init` | K8s 마스터 노드 초기화 |
| `make k8s-join` | K8s 워커 노드 조인 |
| `make reset-pw` | Airflow admin 비밀번호 재설정 |
| `make pgsql` | PostgreSQL 쉘 접속 |

## 🌐 서비스 접속 정보

Traefik 프록시를 통해 로컬 도메인으로 각 서비스에 접속할 수 있습니다.

| 서비스 | 접속 URL | 설명 |
|--------|----------|------|
| **Airflow** | http://af.localhost | 워크플로우 관리 대시보드 |
| **Traefik Dash** | http://dash.localhost/dashboard/ | 프록시 라우팅 상태 대시보드 |
| **pgAdmin** | http://pg.localhost | PostgreSQL 관리 UI (`pg-ui` 프로필 필요) |
| **Mongo Express** | http://me.localhost | MongoDB 관리 UI (`mongo-ui` 프로필 필요) |
| **Kasm** | http://kasm.localhost | VDI 데스크탑 환경 (현재 주석 처리됨) |

## 🧪 개발 워크플로우 (TDD)

1. **Model & Test**: 모델 정의 및 실패하는 테스트 작성. 로컬 샘플 파일(`tests/site/{source}/`)을 사용하여 실제 HTML 구조 기반 테스트를 작성합니다.
2. **Green Logic**: 최소한의 파싱 로직 구현. 하드코딩된 Mock 데이터 사용을 금지합니다.
3. **Golden Record**: 실제 데이터를 JSON 기대값으로 저장하여 회귀 테스트를 수행합니다.
4. **Refactor**: 코드 최적화 및 추상화. `BaseScraper`를 통한 인터페이스 표준화.
5. **Deploy**: Airflow DAG 반영 및 실행 확인.

## 📝 라이선스
[LICENSE](./LICENSE) 파일을 참조하십시오.
