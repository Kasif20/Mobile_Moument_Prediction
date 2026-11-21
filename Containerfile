FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

COPY . /app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	libgomp1 \
	&& rm -rf /var/lib/apt/lists/*

RUN uv sync --locked

EXPOSE 8000

CMD ["uv","run","/app/src/inferance.py"]
