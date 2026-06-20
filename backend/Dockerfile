FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

COPY . .

RUN uv sync --frozen

CMD uv run alembic upgrade head && uv run -m src.utils.init_password && uv run -m src.main
