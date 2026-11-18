# syntax=docker/dockerfile:1

# ---------- base: общее для всех окружений ----------
FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.10.3 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Приложение работает не от root
RUN useradd --system --create-home --uid 1000 app \
    && mkdir /app \
    && chown app:app /app

WORKDIR /app
USER app

COPY --chown=app:app pyproject.toml uv.lock ./


# ---------- dev: dev-зависимости (pytest, ruff, mypy, bandit), автоперезагрузка ----------
FROM base AS dev

RUN uv sync --frozen --no-install-project

COPY --chown=app:app alembic.ini ./
COPY --chown=app:app src ./src
COPY --chown=app:app tests ./tests

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ---------- prod: только runtime-зависимости ----------
FROM base AS prod

RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=app:app alembic.ini ./
COPY --chown=app:app src ./src

EXPOSE 8000
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
