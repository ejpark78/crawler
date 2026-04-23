# Docker 인프라 구성 가이드

이 디렉토리는 크롤러 프로젝트의 실행 및 관리를 위한 모든 Docker 관련 설정과 빌드 자산을 포함하고 있습니다. 최신 Docker Compose의 `include` 기능을 활용하여 모듈화된 인프라 구조를 지향합니다.

## 📂 디렉토리 구조

```text
docker/
├── services/            # [Build & Config] 서비스별 독립 설정 및 빌드 리소스
│   ├── airflow/         # Airflow 스케줄러 및 웹서버 설정 (compose.yml 포함)
│   ├── app/             # 크롤러 워커(Worker) 이미지 빌드 및 설정
│   ├── kasm/            # Kasm 배스천 호스트 (VDI 환경, 한글 입력 지원)
│   ├── kubernetes/      # Kubernetes(Kind 기반) 노드 구성 및 설정 (.env 포함)
│   ├── mongo/           # MongoDB 및 관리 UI 설정
│   ├── traefik/         # Traefik 리버스 프록시 및 라우팅 설정
│   └── wsl/             # WSL 환경용 유틸리티 및 워커 설정
├── compose.crawler.yml  # [Main] 크롤러 프로젝트 메인 진입점
├── compose.kubernetes.yml # [Main] Kubernetes 환경 테스트 진입점
├── .env                 # 기본 환경 변수 설정 파일
└── services/kubernetes/.env # K8s 환경 전용 환경 변수 설정 파일
```

---

## 🚀 주요 구성 요소 설명

### 1. 진입점 (Entry Points)
각 환경에 맞춰 필요한 서비스들을 조합하여 전체 시스템을 구성합니다.
*   **`compose.crawler.yml`**: 데이터 수집을 위한 핵심 인프라(Airflow, MongoDB, Kasm, Traefik 등)를 한 번에 실행합니다.
*   **`compose.kubernetes.yml`**: 로컬 K8s 환경을 구축하고 테스트하기 위한 전용 설정입니다.

### 2. 서비스 모듈 (`services/*/compose.yml`)
시스템의 각 기능을 독립적인 디렉토리로 분리한 것입니다.
*   **Kasm (Bastion Host)**: 브라우저 기반 GUI 환경을 제공하여 내부 네트워크 도구(Chrome, MongoDB Compass, VS Code 등)를 안전하게 사용할 수 있습니다. 한글 입력(Fcitx)이 지원됩니다.
*   **Airflow**: 워크플로우 관리 및 스케줄링을 담당하며, PostgreSQL을 메타데이터 저장소로 사용합니다.
*   **Traefik**: 서비스들의 외부 노출 및 도메인 기반 라우팅을 자동으로 처리합니다.
*   **WSL**: WSL2 환경에서 특정 작업을 수행하거나 최적화된 워커 이미지를 제공합니다.

---

## 🌐 서비스 접속 정보

Traefik을 통해 로컬 도메인으로 각 서비스에 접속할 수 있습니다.

| 서비스 | 접속 URL | 설명 |
| :--- | :--- | :--- |
| **Kasm** | [http://kasm.localhost](http://kasm.localhost) | VDI 데스크탑 환경 (비밀번호는 `.env` 확인) |
| **Airflow** | [http://af.localhost](http://af.localhost) | 워크플로우 관리 대시보드 |
| **pgAdmin** | [http://pg.localhost](http://pg.localhost) | PostgreSQL 관리 UI (`pg-ui` 프로필 필요) |
| **Mongo Express** | [http://me.localhost](http://me.localhost) | MongoDB 관리 UI (`mongo-ui` 프로필 필요) |

---

## 🛠️ 실행 방법

프로젝트 루트(Root)에 위치한 `Makefile`을 이용하거나, 아래와 같이 직접 Docker Compose 명령을 실행할 수 있습니다.

### 크롤러 인프라 실행
```bash
# 기본 실행 (Airflow, MongoDB, Kasm, Traefik 등)
docker compose -f docker/compose.crawler.yml up -d

# 관리 UI(Mongo Express, pgAdmin)를 포함하여 실행
docker compose -f docker/compose.crawler.yml --profile mongo-ui --profile pg-ui up -d
```

### Kubernetes 환경 실행
```bash
docker compose --env-file docker/services/kubernetes/.env -f docker/compose.kubernetes.yml up -d
```

---

## 💡 관리자 가이드

*   **새로운 서비스 추가**: `services/` 폴더에 서비스 디렉토리를 생성하고 `Dockerfile`과 `compose.yml`을 작성한 뒤, 메인 진입점(`compose.crawler.yml` 등)에서 `include` 하십시오.
*   **네트워크 구성**: 모든 서비스는 기본적으로 Traefik을 통해 외부와 통신하며, 내부적으로는 서비스 이름을 호스트명으로 사용하여 서로 통신합니다.
*   **볼륨 데이터**: 데이터베이스 및 로그 파일은 프로젝트 루트의 `volumes/` 디렉토리에 호스트와 바인딩되어 영구 저장됩니다.
