# Docker 인프라 구성 가이드

이 디렉토리는 크롤러 프로젝트의 실행 및 관리를 위한 모든 Docker 관련 설정과 빌드 자산을 포함하고 있습니다. 최신 Docker Compose의 `include` 기능을 활용하여 모듈화된 인프라 구조를 지향합니다.

## 📂 디렉토리 구조

```text
docker/
├── services/            # [Build & Config] 서비스별 독립 설정 및 빌드 리소스
│   ├── airflow/         # Airflow 스케줄러 및 웹서버 설정 (compose.yml 포함)
│   ├── app/             # 크롤러 워커(Worker) 이미지 빌드 및 설정
│   ├── kubernetes/      # Kubernetes(Kind 기반) 노드 구성 및 설정
│   ├── mongo/           # MongoDB 및 관리 UI 설정
│   ├── traefik/         # Traefik 리버스 프록시 및 라우팅 설정
│   └── ...
├── compose.crawler.yml  # [Main] 크롤러 프로젝트 메인 진입점
├── compose.kubernetes.yml # [Main] Kubernetes 환경 테스트 진입점
├── .env                 # 기본 환경 변수 설정 파일
└── .env.k8s             # K8s 환경 전용 환경 변수 설정 파일
```

---

## 🚀 주요 구성 요소 설명

### 1. 진입점 (Entry Points)
각 환경에 맞춰 필요한 서비스들을 조합하여 전체 시스템을 구성합니다.
*   **`compose.crawler.yml`**: 데이터 수집을 위한 핵심 인프라(Airflow, MongoDB, Traefik 등)를 한 번에 실행합니다.
*   **`compose.kubernetes.yml`**: 로컬 K8s 환경을 구축하고 테스트하기 위한 전용 설정입니다.

### 2. 서비스 모듈 (`services/*/compose.yml`)
시스템의 각 기능을 독립적인 디렉토리로 분리한 것입니다. 각 디렉토리의 `compose.yml`은 `include` 지시어를 통해 메인 진입점에서 통합됩니다.
*   **역할**: 서비스 정의, 포트 바인딩, 볼륨 매핑, 이미지 빌드 등

---

## 🛠️ 실행 방법

프로젝트 루트(Root)에 위치한 `Makefile`을 이용하거나, 아래와 같이 직접 Docker Compose 명령을 실행할 수 있습니다.

### 크롤러 인프라 실행
```bash
# 기본 실행
docker compose -f docker/compose.crawler.yml up -d

# 관리 UI(Mongo Express, pgAdmin)를 포함하여 실행
docker compose -f docker/compose.crawler.yml --profile mongo-ui --profile pg-ui up -d
```

### Kubernetes 환경 실행
```bash
docker compose --env-file docker/.env.k8s -f docker/compose.kubernetes.yml up -d
```

---

## 💡 관리자 가이드

*   **새로운 서비스 추가**: `services/` 폴더에 서비스 디렉토리를 생성하고 `Dockerfile`과 `compose.yml`을 작성한 뒤, 메인 진입점(`compose.crawler.yml` 등)에서 `include` 하십시오.
*   **네트워크 구성**: 모든 서비스는 기본적으로 Traefik을 통해 외부와 통신하며, 내부적으로는 서비스 이름을 호스트명으로 사용하여 서로 통신합니다.
*   **볼륨 데이터**: 데이터베이스 및 로그 파일은 프로젝트 루트의 `volumes/` 디렉토리에 호스트와 바인딩되어 영구 저장됩니다.
