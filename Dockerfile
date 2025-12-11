FROM python:3.12-slim AS builder-image

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

RUN uv pip install --system --compile-bytecode \
    --index-url https://download.pytorch.org/whl/cu118 \
    "torch==2.7.1+cu118"

RUN uv pip install --system --compile-bytecode \
    --extra-index-url https://pypi.org/simple/ \
    transformers>=4.53.2

FROM builder-image as dev
WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system --compile-bytecode \
    --extra-index-url https://pypi.org/simple/ \
    .

COPY ./src ./src
EXPOSE 8000
