FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY apps ./apps
COPY pipeline ./pipeline

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

