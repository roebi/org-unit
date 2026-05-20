FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir --upgrade pip==26.1.1 && \
    pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml .
COPY README.md .

RUN uv pip install --system --no-cache-dir -r pyproject.toml

COPY src/ src/
COPY static/ static/

RUN uv pip install --system --no-cache-dir --no-deps .
RUN uv pip install --system --no-cache-dir pytest pytest-asyncio httpx
RUN pytest
RUN uvx --with "pip-audit==2.10.0" pip-audit --skip-editable

FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir --upgrade pip==26.1.1 && \
    pip install --no-cache-dir "uv==0.11.14"

COPY pyproject.toml .
COPY README.md .

RUN uv pip install --system --no-cache-dir -r pyproject.toml

COPY src/ src/
COPY static/ static/

RUN uv pip install --system --no-cache-dir --no-deps .
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "org_unit.main:app", "--host", "0.0.0.0", "--port", "8000"]

