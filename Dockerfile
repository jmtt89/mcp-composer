FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000

RUN apk add --no-cache \
    nodejs \
    npm \
    docker-cli \
    curl

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv venv && uv sync --frozen

# Copy source code
COPY src/ ./src/
COPY mcp_servers.example.json ./mcp_servers.json

EXPOSE 8000

CMD ["uv", "run", "src/main.py"]
