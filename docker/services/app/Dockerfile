# 크롤러 애플리케이션용 맞춤형 이미지
# 이 Dockerfile은 uv와 Playwright(Chromium)를 활용하여 고성능 크롤링 환경을 구축합니다.
# 멀티스테이지 빌드를 통해 최종 이미지 크기를 최적화합니다.

# --- Stage 1: 빌드 단계 (Builder) ---
FROM python:3.12-slim AS builder

ENV UV_LINK_MODE=copy

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Chromium 설치를 위한 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Playwright를 통해 Chromium 설치 (Shadowing 방지를 위해 /app 외부 경로에 설치)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN uv run playwright install chromium

# --- Stage 2: 최종 실행 단계 (Final) ---
FROM python:3.12-slim

ENV UV_LINK_MODE=copy

WORKDIR /app

# Chromium 실행을 위한 런타임 의존성 설치 (이미지 크기 최소화)
RUN apt-get update && apt-get install -y \
    libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libxfixes3 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 빌드 단계에서 생성된 가상환경 및 브라우저 복사
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /ms-playwright /ms-playwright

# 가상환경 사용을 위한 환경 변수 설정
ENV PATH="/app/.venv/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY . .

# undetected-chromedriver가 chromium을 쉽게 찾을 수 있도록 심볼릭 링크 생성
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome

# CMD ["tail", "-f", "/dev/null"]
