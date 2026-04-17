# --- Stage 1: Docker CLI binary extraction ---
FROM docker:latest AS docker-cli-bin

# --- Stage 2: Docker Compose binary download (Safe extraction) ---
FROM alpine:latest AS compose-downloader
RUN apk add --no-cache curl
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /docker-compose && chmod +x /docker-compose

# --- Stage 3: Final Airflow image ---
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
