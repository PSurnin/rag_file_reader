FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system --compile-bytecode \
    --extra-index-url https://pypi.org/simple/ \
    .

COPY ./src ./src
EXPOSE 8000
