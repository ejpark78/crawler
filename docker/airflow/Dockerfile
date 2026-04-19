# 크롤러 프로젝트를 위한 Airflow 맞춤형 이미지
# 이 Dockerfile은 Airflow 내에서 Docker 및 Docker Compose 명령을 실행할 수 있도록
# 필요한 바이너리를 포함하여 이미지를 빌드합니다.

# --- Stage 1: Docker CLI 바이너리 추출 ---
FROM docker:latest AS docker-cli-bin

# --- Stage 2: Docker Compose 바이너리 다운로드 (안전한 추출) ---
FROM alpine:latest AS compose-downloader
RUN apk add --no-cache curl
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /docker-compose && chmod +x /docker-compose

# --- Stage 3: 최종 Airflow 이미지 ---
FROM apache/airflow:2.10.2

USER root

# 1. Docker CLI 복사
COPY --from=docker-cli-bin /usr/local/bin/docker /usr/local/bin/docker

# 2. Docker Compose 바이너리 복사
RUN mkdir -p /usr/libexec/docker/cli-plugins
COPY --from=compose-downloader /docker-compose /usr/libexec/docker/cli-plugins/docker-compose

# 3. 'docker-compose' 단독 명령어로도 사용할 수 있게 심볼릭 링크 생성
RUN ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

WORKDIR /app

COPY . .
RUN cp -r dags /opt/airflow

USER airflow
