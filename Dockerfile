FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY frontend ./frontend
COPY models ./models
COPY data ./data
COPY scripts ./scripts

RUN uv sync --frozen --no-dev

ENV PORT=8003
EXPOSE 8003

CMD ["sh", "-c", "uv run uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}"]
