# Docker 인프라 구성 가이드

이 디렉토리는 크롤러 프로젝트의 실행 및 관리를 위한 모든 Docker 관련 설정과 빌드 자산을 포함하고 있습니다. 최신 Docker Compose의 `include` 기능을 활용하여 모듈화된 인프라 구조를 지향합니다.

## 📂 디렉토리 구조

```text
docker/
├── services/                  # [Build & Config] 서비스별 독립 설정 및 빌드 리소스
│   ├── airflow/               # Airflow 스케줄러/웹서버 + PostgreSQL + pgAdmin
│   ├── app/                   # 크롤러 워커(Worker) 이미지 빌드 및 설정 (일회성 실행)
│   ├── kasm/                  # Kasm 배스천 호스트 (VDI 환경, 한글 입력 지원)
│   ├── kubernetes/            # Kubernetes(Kind 기반) 노드 구성 및 설정
│   ├── mongo/                 # MongoDB + Mongo Express 관리 UI
│   ├── traefik/               # Traefik 리버스 프록시 및 라우팅 설정
│   └── wsl/                   # WSL2 환경용 워커 이미지 빌드
├── compose.crawler.yml        # [Main] 크롤러 프로젝트 메인 진입점
├── compose.kubernetes.yml     # [Main] Kubernetes 환경 테스트 진입점
├── Makefile                   # Docker 네트워크 관리 등 공통 명령어
├── .env                       # 기본 환경 변수 설정 파일
└── services/kubernetes/.env   # K8s 환경 전용 환경 변수 설정 파일
```

---

## 🚀 주요 구성 요소 설명

### 1. 진입점 (Entry Points)

각 환경에 맞춰 필요한 서비스들을 조합하여 전체 시스템을 구성합니다.

*   **`compose.crawler.yml`**: 데이터 수집을 위한 핵심 인프라(Airflow, MongoDB, Traefik, Worker 등)를 한 번에 실행합니다.
    - `include` 지시어를 통해 `services/traefik`, `services/mongo`, `services/airflow`, `services/app`를 통합합니다.
    - `services/kasm`은 현재 주석 처리되어 있으며, 필요시 `include`에 추가하여 활성화할 수 있습니다.
*   **`compose.kubernetes.yml`**: 로컬 K8s 환경을 구축하고 테스트하기 위한 전용 설정입니다.

### 2. 서비스 모듈 (`services/*/compose.yml`)

시스템의 각 기능을 독립적인 디렉토리로 분리한 것입니다. 각 모듈은 자체 `Dockerfile`과 `compose.yml`을 가지며, 메인 진입점에서 `include`하여 사용합니다.

| 서비스 | 설명 | 주요 포함 요소 |
|--------|------|---------------|
| **Airflow** | 워크플로우 관리 및 스케줄링 | `airflow`(스케줄러+웹서버), `postgres`(메타데이터 DB), `pgadmin`(PostgreSQL 관리 UI) |
| **App (Worker)** | 실제 데이터 수집을 수행하는 일회성 컨테이너 | `worker` 서비스 (Airflow BashOperator 등에서 동적으로 실행) |
| **Mongo** | 수집 데이터 저장 및 관리 | `mongodb`(데이터 저장소), `mongo-express`(웹 기반 관리 UI) |
| **Traefik** | 엣지 게이트웨이 및 라우팅 | `traefik` 리버스 프록시, 동적 설정 파일(`dynamic_conf.yml`) |
| **Kasm** | 브라우저 기반 GUI 개발 환경 (VDI) | Ubuntu 기반 데스크탑, Chrome, VS Code, MongoDB Compass, DBeaver, 한글 입력(Fcitx) |
| **Kubernetes** | K8s 테스트 클러스터 | Kind 기반 K8s 노드, Helm, kubectl, k9s 등 툴킷 |
| **WSL** | WSL2 환경 전용 워커 | WSL2 최적화된 워커 이미지 |

#### 상세 서비스 설명

*   **Airflow (`services/airflow/`)**:
    - 스케줄러와 웹서버를 통합 실행 (`standalone` 모드).
    - 호스트의 `/var/run/docker.sock`을 마운트하여 Worker 컨테이너를 동적으로 생성합니다.
    - PostgreSQL을 메타데이터 저장소로 사용합니다.
    - pgAdmin은 `--profile pg-ui` 옵션으로 선택적으로 실행합니다.

*   **App Worker (`services/app/`)**:
    - Airflow의 BashOperator에서 `docker compose run --rm worker` 형태로 실행되는 일회성 컨테이너입니다.
    - `crawler/worker:latest` 이미지를 사용하며, `restart: no` 설정으로 수집 완료 후 자동 종료됩니다.

*   **Mongo (`services/mongo/`)**:
    - `mongo:latest` 이미지를 사용하여 수집된 크롤링 데이터를 저장합니다.
    - `mongo-express`는 `--profile mongo-ui` 옵션으로 선택적으로 실행합니다.

*   **Traefik (`services/traefik/`)**:
    - `local/traefik:v3.6` 커스텀 이미지를 빌드하여 사용합니다.
    - Docker 라벨 기반 자동 서비스 디스커버리를 지원합니다.
    - `dash.localhost`에서 대시보드에 접속할 수 있습니다.

*   **Kasm (`services/kasm/`) - 현재 비활성화**:
    - 브라우저 기반 GUI 환경을 제공하여 낭비 네트워크 도구를 안전하게 사용할 수 있습니다.
    - 한글 입력(Fcitx)이 지원되며, `volumes/kasm`에 사용자 데이터가 영구 저장됩니다.
    - `compose.crawler.yml`의 `include`에서 주석 처리되어 있으며, 필요시 활성화할 수 있습니다.

*   **WSL (`services/wsl/`)**:
    - WSL2 환경에서 실행할 수 있는 별도의 워커 이미지를 제공합니다.

---

## 🌐 서비스 접속 정보

Traefik을 통해 로컬 도메인으로 각 서비스에 접속할 수 있습니다.

| 서비스 | 접속 URL | 설명 | 활성화 조건 |
|--------|----------|------|------------|
| **Airflow** | http://af.localhost | 워크플로우 관리 대시보드 | 기본 포함 |
| **Traefik Dash** | http://dash.localhost/dashboard/ | 프록시 라우팅 상태 대시보드 | 기본 포함 |
| **pgAdmin** | http://pg.localhost | PostgreSQL 관리 UI | `--profile pg-ui` |
| **Mongo Express** | http://me.localhost | MongoDB 관리 UI | `--profile mongo-ui` |
| **Kasm** | http://kasm.localhost | VDI 데스크탑 환경 | `compose.crawler.yml`에서 `include` 활성화 필요 |

---

## 🛠️ 실행 방법

프로젝트 루트(Root)에 위치한 `Makefile`을 이용하거나, 아래와 같이 직접 Docker Compose 명령을 실행할 수 있습니다.

### 크롤러 인프라 실행

```bash
# 기본 실행 (Airflow, MongoDB, Traefik, Worker 등)
docker compose -f docker/compose.crawler.yml up -d

# 관리 UI(Mongo Express, pgAdmin)를 포함하여 실행
docker compose -f docker/compose.crawler.yml --profile mongo-ui --profile pg-ui up -d

# Kasm VDI를 포함하여 실행 (compose.crawler.yml에서 include 주석 해제 필요)
docker compose -f docker/compose.crawler.yml up -d
```

### Kubernetes 환경 실행

```bash
# Kubernetes 테스트 환경 구동
docker compose --env-file docker/services/kubernetes/.env -f docker/compose.kubernetes.yml up -d
```

### Makefile을 통한 통합 관리

루트 `Makefile`에서 Docker Compose 파일 경로를 자동으로 처리합니다.

```bash
# 기본 인프라
make up
make down
make build
make logs

# K8s 환경
make up PRJ=k8s
make k8s-status
```

---

## 🔧 각 서비스 모듈 상세

### Airflow 모듈 (`services/airflow/`)

```yaml
# 핵심 설정
- image: crawler/airflow:latest
- command: standalone
- volumes:
  - ../../..:/app                    # 프로젝트 소스 마운트
  - ../../../dags:/opt/airflow/dags  # DAG 파일 마운트 (읽기 전용)
  - ${VOLUME_PATH}/airflow/logs:/opt/airflow/logs  # 로그 영구 저장
  - /var/run/docker.sock:/var/run/docker.sock      # Docker 엔진 접근 (Worker 동적 생성)
- labels:
  - traefik.http.routers.airflow.rule=Host(`af.localhost`)
  - traefik.http.services.airflow.loadbalancer.server.port=8080
```

### App Worker 모듈 (`services/app/`)

```yaml
# 핵심 설정
- image: crawler/worker:latest
- build:
    context: ../../..
    dockerfile: docker/services/app/Dockerfile
- restart: no  # 일회성 실행
```

Airflow DAG의 BashOperator에서 다음과 같이 호출됩니다:
```bash
docker compose run --rm worker uv run python -m app.main --source GeekNews --page 1 --date 2026-04-20
```

### Mongo 모듈 (`services/mongo/`)

```yaml
# 핵심 설정
- mongodb:
    image: mongo:latest
    volumes:
      - ${VOLUME_PATH}/mongodb:/data/db
- mongo-express:
    profiles: [mongo-ui]  # 선택적 실행
    labels:
      - traefik.http.routers.mongo-express.rule=Host(`me.localhost`)
```

### Traefik 모듈 (`services/traefik/`)

```yaml
# 핵심 설정
- image: local/traefik:v3.6
- ports:
    - "${TRAEFIK_PORT}:80"
- volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # Docker Provider
- command:
    - --providers.docker=true
    - --providers.docker.exposedbydefault=false
    - --providers.file.filename=/etc/traefik/dynamic_conf.yml
```

---

## 💡 관리자 가이드

*   **새로운 서비스 추가**: `services/` 폴터에 서비스 디렉토리를 생성하고 `Dockerfile`과 `compose.yml`을 작성한 뒤, 메인 진입점(`compose.crawler.yml` 등)에서 `include` 하십시오.
*   **네트워크 구성**: 모든 서비스는 기본적으로 `crawler_default` 네트워크를 공유하며, 서비스 이름을 호스트명으로 사용하여 직접 통신합니다.
*   **볼륨 데이터**: 데이터베이스 및 로그 파일은 환경 변수 `VOLUME_PATH`가 가리키는 디렉토리(기본: `volumes/`)에 호스트와 바인딩되어 영구 저장됩니다.
*   **프로필(Profile) 사용**: 관리 UI(pgAdmin, Mongo Express) 등 선택적 서비스는 `--profile` 옵션을 통해 필요할 때만 실행할 수 있습니다.
*   **Kasm 활성화**: `compose.crawler.yml`에서 `services/kasm/compose.yml`의 주석을 해제하고 `docker compose up -d`를 실행하세요. 비밀번호는 `.env` 파일의 `VNC_PW` 값을 확인하십시오.

---

## 📝 환경 변수

주요 환경 변수는 `docker/.env` 파일에 정의되어 있습니다. (실제 파일은 `.gitignore`에 포함되어 있을 수 있으니 템플릿을 참조하세요.)

| 변수 | 설명 | 예시 |
|------|------|------|
| `VOLUME_PATH` | 호스트 볼륨 마운트 기준 경로 | `./volumes` |
| `TRAEFIK_PORT` | Traefik 외부 노출 포트 | `80` |
| `TRAEFIK_ENABLE_LABEL` | Traefik 라우팅 활성화 라벨 | `traefik.enable` |
| `AIRFLOW__CORE__EXECUTOR` | Airflow 실행자 | `LocalExecutor` |
| `POSTGRES_USER/PASSWORD/DB` | PostgreSQL 인증 정보 | `airflow` |
| `KASM_USER` | Kasm 기본 사용자 | `kasm-user` |
| `VNC_PW` | Kasm VNC 비밀번호 | - |
