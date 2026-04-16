# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies for building/installing chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Install Chromium via playwright (it handles the binary download)
RUN uv run playwright install chromium

# --- Stage 2: Final ---
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies for Chromium (Minimizing image size)
RUN apt-get update && apt-get install -y \
    libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libxfixes3 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Set environment paths to use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

# Create a symbolic link for undetected-chromedriver to find chromium easily
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome

CMD ["tail", "-f", "/dev/null"]
