# Kasm VDI 개발 환경 가이드

이 디렉토리는 Kasm Workspaces를 기반으로 한 컨테이너형 가상 데스크탑(VDI) 환경 설정을 포함하고 있습니다. 브라우저만으로 접속 가능한 강력한 GUI 개발 환경을 제공하며, 필요한 도구들을 모듈별로 선택하여 빌드할 수 있습니다.

## 🏗️ 주요 특징

*   **Ubuntu 24.04 (Noble)** 기반의 최신 런타임 환경
*   **모듈형 구성**: 빌드 인자(`ARG`)를 통해 필요한 개발 도구만 선택적으로 설치 (이미지 크기 최적화 가능)
*   **한글 입력 지원**: Fcitx 입력기가 내장되어 있어 브라우저 내에서 원활한 한글 타이핑이 가능합니다.
*   **풍부한 도구 세트**: VS Code, Chrome, MongoDB Compass, DBeaver 등 주요 개발/관리 도구 지원
*   **로컬 워크스페이스 연동**: 호스트 머신의 프로젝트 디렉토리와 볼륨 마운트를 통해 작업 파일을 공유합니다.

---

## 🌐 접속 정보

Traefik 리버스 프록시를 통해 아래 주소로 접속할 수 있습니다.

*   **URL**: [http://kasm.localhost](http://kasm.localhost)
*   **사용자**: `.env` 파일의 `KASM_USER` (기본값: `kasm-user`)
*   **비밀번호**: `.env` 파일의 `VNC_PW` (기본값: `kasm2026`)

> **참고**: 내부적으로는 6901 포트에서 HTTPS로 실행되지만, Traefik이 이를 처리하여 외부에서는 HTTP(80)로 간편하게 접속할 수 있습니다.

---

## 🛠️ 모듈별 빌드 설정

`compose.yml` 또는 빌드 명령 시 아래의 `ARG` 값을 `true`/`false`로 설정하여 설치 여부를 결정할 수 있습니다.

| 모듈 명칭 | 설명 | 기본값 |
| :--- | :--- | :--- |
| `MODULE_FCITX` | 한글 입력기 (Fcitx) 설치 | `true` |
| `MODULE_CHROME` | Google Chrome 브라우저 | `true` |
| `MODULE_VSCODE` | Visual Studio Code | `true` |
| `MODULE_MONGO_COMPASS` | MongoDB Compass | `true` |
| `MODULE_DBEAVER` | DBeaver (범용 DB 관리자) | `true` |
| `MODULE_DOCKER` | Docker CLI 및 Docker-in-Docker 지원 | `true` |
| `MODULE_NODEJS` | Node.js 및 npm 환경 | `true` |
| `MODULE_K8S_TOOLS` | Kubectl, Helm 등 K8s 관리 도구 | `true` |
| `MODULE_AI_AGENTS` | AI 관련 라이브러리 및 도구 세트 | `true` |

---

## 📂 디렉토리 구조

*   `Dockerfile`: Kasm 기반 커스텀 이미지 빌드 정의
*   `compose.yml`: 서비스 실행 설정 및 환경 변수, 볼륨 매핑 정의
*   `modules/`: 각 기능별 설치 스크립트 (`install.sh`가 이를 통합 관리)
*   `startup/`: 컨테이너 시작 시 실행되는 초기화 스크립트 (권한 설정, 서비스 구동 등)

---

## 🔑 주요 볼륨 매핑

컨테이너의 영속성과 도구 연동을 위해 아래와 같은 주요 볼륨이 매핑되어 있습니다.

*   **Workspace**: 호스트의 프로젝트 루트 디렉토리가 `/home/kasm-user/workspace`로 매핑됩니다.
*   **Kubeconfig**: 클러스터 관리 도구 공유를 위해 `.kube` 디렉토리가 매핑됩니다.
*   **SSH Keys**: 노드 접속 및 Git 연동을 위해 SSH 키가 공유됩니다.
*   **Docker Sock**: 컨테이너 내부에서 호스트의 Docker를 제어할 수 있도록 매핑됩니다.

---

## 📝 참고 사항

*   첫 접속 시 브라우저 보안 경고가 발생할 수 있으나, Traefik 설정이 완료된 후에는 `http://kasm.localhost`를 통해 정상 접속 가능합니다.
*   한글 입력이 안 될 경우, 우측 하단 시스템 트레이의 Fcitx 설정을 확인하십시오. (기본 단축키: `Ctrl + Space` 또는 `Hangul` 키)
